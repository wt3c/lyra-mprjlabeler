# Declarar aqui todas as tasks de consumo do Celery
import logging
import re
from celery import shared_task
from processostjrj.mni import consulta_processo, cria_cliente
from .models import (
    Filtro,
    Documento
)


logger = logging.getLogger(__name__)

def limpar_documentos(m_filtro):
    m_filtro.documento_set.all().delete()


def limpar_documentos(m_filtro):
    m_filtro.documento_set.all().delete()


def parse_documentos(m_filtro):
    m_filtro.arquivo_documentos.open(mode='r')
    retorno = m_filtro.arquivo_documentos.readlines()
    m_filtro.arquivo_documentos.close()
    return retorno


def download_processos(documentos):
    cliente = cria_cliente()
    for numero in documentos:
        logger.info('Baixando %s' % numero)
        processo = consulta_processo(cliente, numero.strip(), movimentos=True, _value_1=[{"incluirCabecalho": True}])
        yield processo
    

def parse_documento(params):
    tipos_movimento, processo = params
    retorno = []
    for tipo in tipos_movimento:
        documentos = filter(
            lambda x: re.findall(tipo.nome_tj, x.movimentoLocal.descricao, re.IGNORECASE),
            [mv for mv in processo.processo.movimento if mv.movimentoLocal]
        )

        for documento in documentos:
            inteiro_teores = filter(
                lambda x: re.findall(r'^Descrição: ', x, re.IGNORECASE),
                documento.complemento
            )
            for inteiro_teor in inteiro_teores:
                retorno.append((processo.processo.dadosBasicos.numero, tipo, inteiro_teor))

    return retorno


def obtem_documentos_finais(pre_documentos, m_filtro):
    for pre_documento in pre_documentos:
        m_documento = Documento()
        m_documento.filtro = m_filtro
        m_documento.numero = pre_documento[0]
        m_documento.tipo_movimento = pre_documento[1]
        m_documento.conteudo = pre_documento[2]
        m_documento.save()


@shared_task
def submeter_classificacao(idfiltro):
    logger.info('Processando filtro %s' % idfiltro)
    m_filtro = Filtro.objects.get(pk=idfiltro)

    # limpando documentos atuais
    limpar_documentos(m_filtro)

    tipos_movimento = m_filtro.tipos_movimento.all()
    logger.info('Parsearei pelos Tipos de Movimento: %s' % str(tipos_movimento))

    # Remove todos os documentos baixados anteriormente
    limpar_documentos(m_filtro)

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
