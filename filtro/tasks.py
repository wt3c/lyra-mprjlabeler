# Declarar aqui todas as tasks de consumo do Celery
import logging
from celery import shared_task
from classificador_lyra.regex import classifica_item_sequencial
from io import BytesIO
from django.core.files import File
from tarfile import TarFile, TarInfo
from collections import defaultdict
from slugify import slugify
from .models import Filtro
from .task_utils import (
    limpar_documentos,
    parse_documentos,
    download_processos,
    parse_documento,
    obtem_documentos_finais,
    montar_estrutura_filtro,
    preparar_classificadores,
    obtem_classe
)


logger = logging.getLogger(__name__)


SITUACOES_EXECUTORES = '246'


@shared_task
def submeter_classificacao(idfiltro):
    logger.info('Processando filtro %s' % idfiltro)
    m_filtro = Filtro.objects.get(pk=idfiltro)

    if m_filtro.situacao in SITUACOES_EXECUTORES:
        return

    m_filtro.situacao = '2'  # baixando
    m_filtro.save()

    # limpando documentos atuais
    limpar_documentos(m_filtro)

    tipos_movimento = m_filtro.tipos_movimento.all()
    logger.info(
        'Parsearei pelos Tipos de Movimento: %s' % str(tipos_movimento)
    )

    # Obtém todos os números de documentos
    numeros_documentos = parse_documentos(m_filtro)

    # Baixa os processos
    processos = []
    contador = 0
    logger.info('Vou baixar %s documentos' % len(numeros_documentos))
    for processo in download_processos(numeros_documentos):
        processos.append(processo)
        contador += 1
        logger.info('Passo %s' % contador)
        m_filtro.percentual_atual = contador / len(numeros_documentos) * 100
        logger.info('Percentual %s' % m_filtro.percentual_atual)
        m_filtro.save()

    # Parse de Documentos
    pre_documentos = []
    for bloco in map(
                parse_documento,
                [(tipos_movimento, processo) for processo in processos]
            ):
        pre_documentos.extend(bloco)

    obtem_documentos_finais(pre_documentos, m_filtro)

    m_filtro.situacao = '3'
    m_filtro.save()

    classificar_baixados.delay(idfiltro)


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

    m_filtro.situacao = '5'
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