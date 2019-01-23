# Declarar aqui todas as tasks de consumo do Celery
from celery import shared_task


@shared_task
def exemplo():
    pass
