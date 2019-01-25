# Declarar aqui todas as tasks de consumo do Celery
import logging
import re
from celery import shared_task
from processostjrj.mni import consulta_processo, cria_cliente
from slugify import slugify
from .models import (
    Filtro,
    Documento
)
from classificador_lyra.regex import (
    classifica_item_sequencial,
    constroi_classificador_dinamica
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


BASE_CLASSIFICADOR = {
            "nome":None,
            "parametros": {
                "regex": [],
                "regex_reforco": None,
                "regex_exclusao": None,
                "regex_invalidacao": None,
                "coadunadas": None
            }
        }


def transforma_em_regex(itemfiltro):
    if itemfiltro.regex:
        return '(%s)' % itemfiltro.termos
    else:
        return '(%s)' % re.escape(itemfiltro.termos)



def montar_estrutura_filtro(m_filtro):
    retorno = []
    for classe in m_filtro.classefiltro_set.all():
        pre_classe = {
            "nome":None,
            "classe": classe,
            "parametros": {
                "regex": [],
                "regex_reforco": None,
                "regex_exclusao": None,
                "regex_invalidacao": None,
                "coadunadas": None
            }
        }

        pre_classe['nome'] = slugify(classe.nome).replace('-', '_')
        pre_classe['parametros']['regex'] = list(map(
            transforma_em_regex, filter(lambda x: x.tipo == '1', classe.itemfiltro_set.all())))
        pre_classe['parametros']['regex_reforco'] = list(map(
            transforma_em_regex, filter(lambda x: x.tipo == '2', classe.itemfiltro_set.all())))
        pre_classe['parametros']['regex_exclusao'] = list(map(
            transforma_em_regex, filter(lambda x: x.tipo == '3', classe.itemfiltro_set.all())))
        pre_classe['parametros']['regex_invalidacao'] = list(map(
            transforma_em_regex, filter(lambda x: x.tipo == '4', classe.itemfiltro_set.all())))
        pre_classe['parametros']['coadunadas'] = list(map(
            transforma_em_regex, filter(lambda x: x.tipo == '5', classe.itemfiltro_set.all())))

        retorno.append(pre_classe)
    
    return retorno


def preparar_classificadores(estrutura):
    return [
        constroi_classificador_dinamica(item['nome'], item['parametros'])
        for item in estrutura
    ]


def obtem_classe(classificacao, estrutura):
    return next(
        filter(
            lambda x: x['nome'] == classificacao['classificacao'].__class__.__name__,
            estrutura
        )
    )["classe"]


@shared_task
def classificar_baixados(idfiltro):
    logger.info('Classificando filtro %s' % idfiltro)
    m_filtro = Filtro.objects.get(pk=idfiltro)

    # monta a estrutura de classificadores
    estrutura = montar_estrutura_filtro(m_filtro)

    # prepara os classificadores dinâmicos
    classificadores = preparar_classificadores(estrutura)

    # roda os classificadores por 
    for documento in m_filtro.documento_set.all():
        classificacao = classifica_item_sequencial(
            documento.conteudo,
            classificadores
        )
        if classificacao:
            documento.classe_filtro = obtem_classe(classificacao, estrutura)
            documento.save()
        
