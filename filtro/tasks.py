# Declarar aqui todas as tasks de consumo do Celery
import logging
from celery import shared_task
from classificador_lyra.regex import classifica_item_sequencial
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


@shared_task
def submeter_classificacao(idfiltro):
    logger.info('Processando filtro %s' % idfiltro)
    m_filtro = Filtro.objects.get(pk=idfiltro)

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
    processos = download_processos(numeros_documentos)

    # Parse de Documentos
    pre_documentos = []
    for bloco in map(
                parse_documento,
                [(tipos_movimento, processo) for processo in processos]
            ):
        pre_documentos.extend(bloco)

    obtem_documentos_finais(pre_documentos, m_filtro)


@shared_task
def classificar_baixados(idfiltro):
    logger.info('Classificando filtro %s' % idfiltro)
    m_filtro = Filtro.objects.get(pk=idfiltro)

    # monta a estrutura de classificadores
    estrutura = montar_estrutura_filtro(m_filtro)

    # prepara os classificadores dinâmicos
    classificadores = preparar_classificadores(estrutura)

    # roda os classificadores
    for documento in m_filtro.documento_set.all():
        classificacao = classifica_item_sequencial(
            documento.conteudo,
            classificadores
        )
        if classificacao:
            documento.classe_filtro = obtem_classe(classificacao, estrutura)
            documento.save()
