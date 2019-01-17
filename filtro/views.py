from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from .forms import AdicionarFiltroForm, FiltroForm
from .models import Filtro


@login_required
def filtros(request):
    novo_filtro_form = AdicionarFiltroForm

    return render(
        request,
        'filtro/filtros.html',
        {
            'filtros': Filtro.objects.all(),
            'novofiltroform': novo_filtro_form
        }
    )


@login_required
@require_http_methods(['POST'])
def adicionar_filtro(request):
    form = AdicionarFiltroForm(request.POST)

    form.save()

    return redirect(
        reverse(
            'filtros-filtro',
            args=[form.instance.id]
        )
    )


@login_required
def filtro(request, idfiltro):
    m_filtro = Filtro.objects.get(pk=idfiltro)
    form = FiltroForm(instance=m_filtro)

    if request.method == 'POST':
        form = FiltroForm(request.POST, request.FILES, instance=m_filtro)
        form.save()

    return render(
        request,
        'filtro/filtro.html',
        {
            'form': form,
            'model': m_filtro,
        }
    )
