"Limpa um conjunto de tarefas de uma campanha caso não tenha Respostas"
from django.core.management.base import BaseCommand
from labeler.models import Tarefa


class Command(BaseCommand):
    "apaga as tarefas de uma campanha e todas as suas respostas"

    help = __doc__

    def add_arguments(self, parser):
        "Configura os parâmetros e opçẽos"
        parser.add_argument('id_campanha', nargs=1, type=int)

    def handle(self, *args, **options):
        "Executa o comando de limpeza de tarefas"
        del args
        id_campanha = options['id_campanha'][0]

        Tarefa.objects.filter(campanha__id=id_campanha).delete()
