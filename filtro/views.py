from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Filtro


def filtros(request):


    return render(
        request,
        'filtro/filtros.html',
        {
            'filtros': Filtro.objects.all()
        }
    )