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
        except:
            raise CommandError("O ID de campanha informado não existe")


        arquivo = json.load(open(arquivo))

        for item in arquivo:
            tarefa = Tarefa()
            tarefa.campanha = campanha
            tarefa.texto_original = item['original']
            tarefa.texto_inteligencia = item['parseado']
            tarefa.save()