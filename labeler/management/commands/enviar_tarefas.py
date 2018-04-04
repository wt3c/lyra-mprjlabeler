"Envia tarefas para um servidor remoto, de 100 em 100"
import json
import requests
from django.core.management.base import BaseCommand

from multiprocessing import Pool

ID_CAMPANHA = None
ENDERECOREMOTO = None
STDOUT = None
STYLE = None

QUANTIDADE_TAREFAS = 50
QUANTIDADE_THREADS = 12


class Command(BaseCommand):
    "Envia tarefas para um servidor remoto, de 1000 em 1000"

    help = __doc__

    def add_arguments(self, parser):
        "Configura os parâmetros e opções"
        parser.add_argument('id_campanha', nargs=1, type=int)
        parser.add_argument('arquivo', nargs=1, type=str)
        parser.add_argument('enderecoremoto', nargs=1, type=str)

    def handle(self, *args, **options):
        "Executa o envio de tarefas"
        global ID_CAMPANHA, ENDERECOREMOTO, STDOUT, STYLE, QUANTIDADE_THREADS
        del args
        ID_CAMPANHA = options['id_campanha'][0]
        arquivo = options['arquivo'][0]
        ENDERECOREMOTO = options['enderecoremoto'][0]
        STDOUT = self.stdout
        STYLE = self.style

        arquivo = json.load(open(arquivo))

        novo = []
        while arquivo:
            novo += [pop(arquivo, QUANTIDADE_TAREFAS)]
        arquivo = novo

        pool = Pool(QUANTIDADE_THREADS)
        pool.map(envia, arquivo)


def pop(lista, qtd):
    temp = lista[:qtd]
    del lista[:qtd]
    return temp


def envia(lista):
    global ID_CAMPANHA, ENDERECOREMOTO, STDOUT, STYLE, QUANTIDADE_TAREFAS
    tentativas = 0
    response = None
    while True:
        STDOUT.write(STYLE.SUCCESS('Comecei!'))
        try:
            response = requests.post(
                "%sapi/tarefa/%s/" % (ENDERECOREMOTO, ID_CAMPANHA),
                data=json.dumps(lista))
            STDOUT.write(STYLE.SUCCESS('Enviei'))
            break
        except Exception as error:
            if tentativas > 3:
                STDOUT.write(STYLE.ERROR(
                    "Desisti"))
                break
            STDOUT.write(STYLE.ERROR(
                "Deu ruim - %s" % tentativas))
            tentativas += 1

    if response and response.status_code == 200:
        STDOUT.write(STYLE.SUCCESS('%s tarefas enviads' % QUANTIDADE_TAREFAS))
    else:
        if response:
            STDOUT.write(STYLE.ERROR(response.content))
        else:
            STDOUT.write(STYLE.ERROR("Quebrou geral"))
