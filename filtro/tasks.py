# Declarar aqui todas as tasks de consumo do Celery
import csv
import ctypes
import logging
from collections import defaultdict
from io import BytesIO, TextIOWrapper
from tarfile import TarFile, TarInfo

import urllib3
from billiard.pool import Pool, cpu_count
from celery import shared_task
from classificador_lyra.regex import classifica_item_sequencial
from django.conf import settings
from django.core.files import File
from slugify import slugify
import chardet

from .analysis import modelar_lda
from .models import Documento, Filtro
from .task_utils import (
    download_processos,
    limpar_documentos,
    montar_estrutura_filtro,
    obtem_classe,
    obtem_documento_final,
    parse_documento,
    parse_documentos,
    preparar_classificadores,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


logger = logging.getLogger(__name__)
# configuracao de tamanho maximo de campo csv disponivel na arquitetura
csv.field_size_limit(int(ctypes.c_ulong(-1).value // 2))


SITUACOES_EXECUTORES = "246"


class NullBytesIOWrapper(TextIOWrapper):
    def readline(self, *args, **kwargs):
        data = super().readline(*args, **kwargs)
        return data.replace("\x00", "").replace("\xa0", " ")


def submeter_classificacao_tjrj(m_filtro, idfiltro):
    tipos_movimento = m_filtro.tipos_movimento.all()
    logger.info(
        "Parsearei pelos Tipos de Movimento: %s" % str(tipos_movimento)
    )

    # Obtém todos os números de documentos
    numeros_documentos = parse_documentos(m_filtro)

    # Baixa os processos
    contador = 0
    logger.info("Vou baixar %s documentos" % len(numeros_documentos))
    trazer_iniciais = tipos_movimento.filter(
        nome=settings.NOME_FILTRO_PETICAO_INICIAL
    ).exists()
    for numero, processo, iniciais in download_processos(
        numeros_documentos, trazer_iniciais=trazer_iniciais
    ):
        contador += 1
        logger.info("Passo %s, processo %s" % (contador, numero))

        try:
            promessas = parse_documento(tipos_movimento, processo)
            obtem_documento_final(promessas, m_filtro)
            if iniciais:
                obtem_documento_final(
                    iniciais, m_filtro,
                )

        except Exception as error:
            print(str(error))

        m_filtro.percentual_atual = contador / len(numeros_documentos) * 100
        logger.info("Percentual %s" % m_filtro.percentual_atual)
        m_filtro.save()

    m_filtro.situacao = "3"
    m_filtro.save()

    classificar_baixados.delay(idfiltro)


def submeter_classificacao_arquivotabulado(m_filtro, idfiltro):
    logger.info("Vou parsear os documentos")

    with m_filtro.arquivo_documentos.open(mode="rb") as f_in:
        enc = chardet.detect(f_in.readline())['encoding']
        f_in.seek(0)
        f_in = NullBytesIOWrapper(f_in, enc)

        dialect = csv.Sniffer().sniff(f_in.read(4096), delimiters=",;")
        f_in.seek(0)

        logger.info("Encoding encontrado: {}".format(enc))
        logger.info(
            "Dialect info: delimiter {} -escapechar {} -quotechar {}".format(
                dialect.delimiter, dialect.escapechar, dialect.quotechar
            )
        )

        reader = csv.reader(f_in, dialect)
        for linha in reader:
            m_documento = Documento()
            m_documento.filtro = m_filtro
            m_documento.numero = linha[0]
            m_documento.conteudo = linha[1]
            m_documento.save()

    logger.info("Terminei de parsear os documentos")

    m_filtro.situacao = "3"
    m_filtro.save()

    classificar_baixados.delay(idfiltro)


@shared_task
def submeter_classificacao(idfiltro):
    logger.info("Processando filtro %s" % idfiltro)
    m_filtro = Filtro.objects.get(pk=idfiltro)

    if m_filtro.situacao in SITUACOES_EXECUTORES:
        return

    m_filtro.situacao = "2"  # baixando
    m_filtro.save()

    # limpando documentos atuais
    limpar_documentos(m_filtro)

    if m_filtro.tipo_raspador == "1":
        submeter_classificacao_tjrj(m_filtro, idfiltro)
    elif m_filtro.tipo_raspador == "2":
        submeter_classificacao_arquivotabulado(m_filtro, idfiltro)


estrutura_global = None
classificadores_global = None


def classificador_inicializador(estrutura_base):
    global estrutura_global, classificadores_global
    estrutura_global = estrutura_base

    # prepara os classificadores dinâmicos
    classificadores_global = preparar_classificadores(estrutura_global)


def classificar_paralelo(documento):
    try:
        classificacao = classifica_item_sequencial(
            documento.conteudo, classificadores_global
        )
        if classificacao:
            documento.classe_filtro = obtem_classe(
                classificacao, estrutura_global
            )
        else:
            documento.classe_filtro = None
    except Exception as error:
        return error

    return documento


@shared_task
def classificar_baixados(idfiltro):
    logger.info("Classificando filtro %s" % idfiltro)
    m_filtro = Filtro.objects.get(pk=idfiltro)

    if m_filtro.situacao in SITUACOES_EXECUTORES:
        return

    m_filtro.situacao = "4"
    m_filtro.percentual_atual = 0
    m_filtro.save()

    # monta a estrutura de classificadores
    estrutura = montar_estrutura_filtro(m_filtro)

    documentos = m_filtro.documento_set.all()
    iterador = documentos.iterator()
    logger.info("Contando a quantidade de documento")
    qtd_documentos = documentos.count()
    pool = Pool(
        cpu_count(),
        initializer=classificador_inicializador,
        initargs=(estrutura,),
    )

    contador = 0
    logger.info(
        "Aplicando classificadores em paralelo: %s chunks em %s nucleos"
        % (settings.CLASSIFICADOR_CHUNKSIZE, cpu_count())
    )
    for documento in pool.imap(
        classificar_paralelo,
        iterador,
        chunksize=settings.CLASSIFICADOR_CHUNKSIZE,
    ):
        contador += 1
        m_filtro.percentual_atual = contador / qtd_documentos * 100
        if contador % 500 == 0:
            logger.info("Percentual %s" % m_filtro.percentual_atual)
        m_filtro.save()
        documento.save()

    logger.info("Terminei classificação regex, começando LDA")

    # aplica modelo LDA
    aplicar_lda(m_filtro)

    m_filtro.situacao = "5"
    m_filtro.save()


def aplicar_lda(m_filtro):
    conteudos = (
        m_filtro.documento_set.filter(classe_filtro__isnull=True)
        .all()
        .values_list("conteudo", flat=True)
    )

    if len(conteudos) >= settings.MININUM_DOC_COUNT_LDA:
        dados = modelar_lda(conteudos)
    else:
        dados = None

    m_filtro.saida_lda = dados
    m_filtro.save()


@shared_task
def compactar(idfiltro):
    m_filtro = Filtro.objects.get(pk=idfiltro)

    if m_filtro.situacao in SITUACOES_EXECUTORES:
        return

    m_filtro.situacao = "6"
    m_filtro.percentual_atual = 0
    m_filtro.save()

    slug_classificador = slugify(m_filtro.nome)

    documentos = m_filtro.documento_set.all()
    qtd_documentos = documentos.count()

    # cria o streamfile em disco
    nometar = "%s.tar.bz2" % slug_classificador

    numeros_documentos = defaultdict(int)

    with BytesIO() as arquivotar:
        tarfile = TarFile(name=nometar, mode="w", fileobj=arquivotar)

        for contador, documento in enumerate(documentos):
            numero = documento.numero
            numeros_documentos[numero] += 1
            ordem = numeros_documentos[numero]

            with BytesIO() as conteudo_documento:
                conteudo_documento.write(
                    documento.conteudo.encode("latin1", "ignore")
                )
                conteudo_documento.seek(0)

                if documento.classe_filtro:
                    classe = slugify(documento.classe_filtro.nome)
                else:
                    classe = slugify("Não Identificado")

                if documento.tipo_movimento:
                    tipo = slugify(documento.tipo_movimento.nome)
                else:
                    tipo = "documento"

                tarinfo = TarInfo(
                    name="%s/%s-%s-%s.txt" % (classe, tipo, numero, ordem)
                )
                tarinfo.size = len(conteudo_documento.getvalue())
                conteudo_documento.seek(0)

                tarfile.addfile(fileobj=conteudo_documento, tarinfo=tarinfo)

            m_filtro.percentual_atual = contador / qtd_documentos * 100
            logger.info("Percentual %s" % m_filtro.percentual_atual)
            m_filtro.save()

        arquivotar.seek(0)
        m_filtro.saida.save(nometar, File(arquivotar))
        m_filtro.situacao = "7"
        m_filtro.save()
