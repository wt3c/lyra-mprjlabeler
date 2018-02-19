import json
from django.core.management.base import BaseCommand, CommandError
from labeler.models import Tarefa

class Command(BaseCommand):
    "apaga as tarefas de uma campanha e todas as suas respostas"
    
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('id_campanha', nargs=1, type=int)

    def handle(self, *args, **options):
        id_campanha = options['id_campanha'][0]

        Tarefa.objects.filter(campanha__id=id_campanha).delete()