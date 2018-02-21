"APIs do labeler"
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Tarefa, Campanha


@csrf_exempt
@require_http_methods(["POST"])
def tarefa(request, idcampanha):
    "Importa uma lista de tarefas via POST"
    tarefas = json.loads(request.body.decode('utf-8'))
    campanha = get_object_or_404(Campanha, id=idcampanha)

    Tarefa.importar_tarefas(campanha, tarefas)

    return JsonResponse({'ok': True})
