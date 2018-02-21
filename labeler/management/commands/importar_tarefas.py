"Importação de arquivos JSON com Tarefas"
import json
from django.core.management.base import BaseCommand, CommandError
from labeler.models import Campanha, Tarefa


class Command(BaseCommand):
    "importa um json com as tarefas de uma campanha"

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('id_campanha', nargs=1, type=int)
        parser.add_argument('arquivo', nargs=1, type=str)

    def handle(self, *args, **options):
        id_campanha = options['id_campanha'][0]
        arquivo = options['arquivo'][0]

        try:
            campanha = Campanha.objects.get(id=id_campanha)
        except Campanha.DoesNotExist:
            raise CommandError("O ID de campanha informado não existe")

        arquivo = json.load(open(arquivo))

        Tarefa.importar_tarefas(campanha, arquivo)
