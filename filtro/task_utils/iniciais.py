import io
import logging
import re

import requests
from django.conf import settings
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from tqdm import tqdm
from zeep import Client, Transport

from filtro.models import TipoMovimento

logger = logging.getLogger(__name__)


s = requests.Session()
s.verify = False
transport = Transport(session=s)
client = Client(
    "https://webserverseguro.tjrj.jus.br/MNI/Servico.svc?singleWsdl",
    transport=transport,
)


def obter_documentos(processo):
    conteudo = client.service.consultarProcesso(
        idConsultante=settings.ID_MNI,
        senhaConsultante=settings.SENHA_MNI,
        numeroProcesso=processo,
        movimentos=0,
        _value_1={"incluirDocumentos": 1},
    )

    if conteudo["sucesso"] and conteudo["processo"]:
        return conteudo["processo"]["documento"]
    return False


def obter_integra(processo, iddocumento, tqnumeros_documentos):
    tqnumeros_documentos.set_description(f"Baixando íntegra {iddocumento}")
    conteudo = client.service.consultarProcesso(
        idConsultante=settings.ID_MNI,
        senhaConsultante=settings.SENHA_MNI,
        numeroProcesso=processo,
        movimentos=0,
        _value_1={"documento": iddocumento},
    )

    if conteudo["sucesso"]:
        return conteudo["processo"]["documento"][0]["conteudo"]


def mapnow(x, y):
    return list(map(x, y))


def obter_numeros_documentos(documentos, tipo_movimento):
    return mapnow(
        lambda x: x["idDocumento"],
        filter(
            lambda x: re.search(tipo_movimento.nome_tj, x["descricao"].lower()), documentos
        ),
    )


def processar(processo):
    processo = processo.replace("-", "").replace(".", "").split(";")[0].strip()
    tipo_movimento = TipoMovimento.objects.get(
        nome=settings.NOME_FILTRO_PETICAO_INICIAL
    )
    try:
        movimentos = obter_documentos(processo)
        if movimentos:
            numeros_documentos = obter_numeros_documentos(
                movimentos,
                tipo_movimento,
            )
            tqnumeros_documentos = tqdm(numeros_documentos, leave=False)
            integras = mapnow(
                lambda x: obter_integra(processo, x, tqnumeros_documentos),
                tqnumeros_documentos,
            )
            tqintegras = tqdm(list(enumerate(integras)), leave=False)
            iniciais = mapnow(
                lambda x: extrai_integra(
                    processo, x, tqintegras, tipo_movimento
                ),
                tqintegras,
            )
            return iniciais

        else:
            logger.error(f"Nenhum movimento encontrado no processo {processo}")
            return 0
    except Exception as error:
        logger.error("{!r} -> número processo {}".format(error, processo))
        return 0
    return 1


def extrai_integra(processo, params, tqintegras, tipo_movimento):
    seq, integra = params
    buffer_ = io.BytesIO(integra)
    texto = extract_text_from_pdf(buffer_)
    return (processo, tipo_movimento, texto)


def extract_text_from_pdf(fobj):
    parser = PDFParser(fobj)
    doc = PDFDocument(parser)
    text = ""
    for page_number, page in enumerate(PDFPage.create_pages(doc), start=1):
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        result = io.StringIO()
        device = TextConverter(rsrcmgr, result, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        interpreter.process_page(page)
        text += result.getvalue()

    return text
