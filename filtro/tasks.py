# Declarar aqui todas as tasks de consumo do Celery
from celery import shared_task
from .models import Filtro


@shared_task
def submeter_classificacao(idfiltro):
    m_filtro = Filtro.objects.get(pk=idfiltro)
