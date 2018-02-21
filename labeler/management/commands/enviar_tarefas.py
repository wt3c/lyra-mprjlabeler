"Envia tarefas para um servidor remoto, de 100 em 100"
import json
import requests
from django.core.management.base import BaseCommand


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
        del args
        id_campanha = options['id_campanha'][0]
        arquivo = options['arquivo'][0]
        enderecoremoto = options['enderecoremoto'][0]

        arquivo = json.load(open(arquivo))

        while arquivo:
            lista = arquivo[:100]

            response = requests.post(
                "%sapi/tarefa/%s/" % (enderecoremoto, id_campanha),
                data=json.dumps(lista))

            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('100 tarefas enviads'))
            else:
                self.stdout.write(self.style.ERROR(response.content))
                return

            del arquivo[:100]
