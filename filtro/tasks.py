# Declarar aqui todas as tasks de consumo do Celery
import csv
import ctypes
import logging
from celery import shared_task
from classificador_lyra.regex import classifica_item_sequencial
from io import BytesIO
from django.core.files import File
from tarfile import TarFile, TarInfo
from collections import defaultdict
from slugify import slugify
from .models import Filtro, Documento
from .task_utils import (
    limpar_documentos,
    parse_documentos,
    download_processos,
    parse_documento,
    obtem_documento_final,
    montar_estrutura_filtro,
    preparar_classificadores,
    obtem_classe
)
from .analysis import modelar_lda

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


logger = logging.getLogger(__name__)
# configuracao de tamanho maximo de campo csv disponivel na arquitetura
csv.field_size_limit(int(ctypes.c_ulong(-1).value // 2))


SITUACOES_EXECUTORES = '246'


def submeter_classificacao_tjrj(m_filtro, idfiltro):
    tipos_movimento = m_filtro.tipos_movimento.all()
    logger.info(
        'Parsearei pelos Tipos de Movimento: %s' % str(tipos_movimento)
    )

    # conta a quantidade de linhas
    num_lines = sum(1 for line in m_filtro.arquivo_documentos.open(mode='r'))

    # Baixa os processos
    contador = 0
    logger.info('Vou baixar %s documentos' % num_lines)
    for numero, processo, detalhes in download_processos(
            parse_documentos(m_filtro)):
        contador += 1
        logger.info('Passo %s, processo %s' % (contador, numero))

        try:
            promessas = parse_documento(
                tipos_movimento,
                processo
            )
            obtem_documento_final(
                promessas,
                m_filtro,
                detalhes
            )
        except Exception as error:
            logger.error(str(error))

        m_filtro.percentual_atual = contador / num_lines * 100
        logger.info('Percentual %s' % m_filtro.percentual_atual)
        m_filtro.save()

    m_filtro.situacao = '3'
    m_filtro.save()

    classificar_baixados.delay(idfiltro)


def submeter_classificacao_arquivotabulado(m_filtro, idfiltro):
    logger.info('Vou parsear os documentos')

    with m_filtro.arquivo_documentos.open(mode='r') as saidinha:
        reader = csv.reader(saidinha)
        for linha in reader:
            m_documento = Documento()
            m_documento.filtro = m_filtro
            m_documento.numero = linha[0]
            m_documento.conteudo = linha[1]
            m_documento.save()

    logger.info('Terminei de parsear os documentos')

    m_filtro.situacao = '3'
    m_filtro.save()

    classificar_baixados.delay(idfiltro)


@shared_task
def submeter_classificacao(idfiltro):
    logger.info('Processando filtro %s' % idfiltro)
    m_filtro = Filtro.objects.get(pk=idfiltro)

    if m_filtro.situacao in SITUACOES_EXECUTORES:
        return

    #m_filtro.situacao = '2'  # baixando
    #m_filtro.save()

    # limpando documentos atuais
    limpar_documentos(m_filtro)

    if m_filtro.tipo_raspador == '1':
        submeter_classificacao_tjrj(m_filtro, idfiltro)
    elif m_filtro.tipo_raspador == '2':
        submeter_classificacao_arquivotabulado(m_filtro, idfiltro)


@shared_task
def classificar_baixados(idfiltro):
    logger.info('Classificando filtro %s' % idfiltro)
    m_filtro = Filtro.objects.get(pk=idfiltro)

    if m_filtro.situacao in SITUACOES_EXECUTORES:
        return

    m_filtro.situacao = '4'
    m_filtro.percentual_atual = 0
    m_filtro.save()

    # monta a estrutura de classificadores
    estrutura = montar_estrutura_filtro(m_filtro)

    # prepara os classificadores dinâmicos
    classificadores = preparar_classificadores(estrutura)

    documentos = m_filtro.documento_set.all()
    qtd_documentos = documentos.count()

    # roda os classificadores
    for contador, documento in enumerate(documentos):
        classificacao = classifica_item_sequencial(
            documento.conteudo,
            classificadores
        )
        if classificacao:
            documento.classe_filtro = obtem_classe(classificacao, estrutura)
            documento.save()
        else:
            documento.classe_filtro = None
            documento.save()

        m_filtro.percentual_atual = contador / qtd_documentos * 100
        logger.info('Percentual %s' % m_filtro.percentual_atual)
        m_filtro.save()

    # aplica modelo LDA
    aplicar_lda(m_filtro)

    m_filtro.situacao = '5'
    m_filtro.save()


def aplicar_lda(m_filtro):
    conteudos = m_filtro.documento_set.filter(
        classe_filtro__isnull=True).all().values_list('conteudo', flat=True)

    dados = modelar_lda(conteudos)

    m_filtro.saida_lda = dados
    m_filtro.save()


@shared_task
def compactar(idfiltro):
    m_filtro = Filtro.objects.get(pk=idfiltro)

    if m_filtro.situacao in SITUACOES_EXECUTORES:
        return

    m_filtro.situacao = '6'
    m_filtro.percentual_atual = 0
    m_filtro.save()

    slug_classificador = slugify(m_filtro.nome)

    documentos = m_filtro.documento_set.all()
    qtd_documentos = documentos.count()

    # cria o streamfile em disco
    nometar = '%s.tar.bz2' % slug_classificador

    numeros_documentos = defaultdict(int)

    with BytesIO() as arquivotar:
        tarfile = TarFile(
            name=nometar,
            mode='w',
            fileobj=arquivotar
        )

        for contador, documento in enumerate(documentos):
            numero = documento.numero
            numeros_documentos[numero] += 1
            ordem = numeros_documentos[numero]

            with BytesIO() as conteudo_documento:
                conteudo_documento.write(
                    documento.conteudo.encode('latin1')
                )
                conteudo_documento.seek(0)

                if documento.classe_filtro:
                    classe = slugify(documento.classe_filtro.nome)
                else:
                    classe = slugify("Não Identificado")

                tipo = slugify(documento.tipo_movimento.nome)

                tarinfo = TarInfo(
                    name='%s/%s-%s-%s.txt' % (
                        classe,
                        tipo,
                        numero,
                        ordem
                    )
                )
                tarinfo.size = len(conteudo_documento.getvalue())
                conteudo_documento.seek(0)

                tarfile.addfile(fileobj=conteudo_documento, tarinfo=tarinfo)

            m_filtro.percentual_atual = contador / qtd_documentos * 100
            logger.info('Percentual %s' % m_filtro.percentual_atual)
            m_filtro.save()

        arquivotar.seek(0)
        m_filtro.saida.save(nometar, File(arquivotar))
        m_filtro.situacao = '7'
        m_filtro.save()
