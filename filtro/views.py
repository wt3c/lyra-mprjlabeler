from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
    get_list_or_404
)
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from .forms import AdicionarFiltroForm, FiltroForm
from .models import Filtro


def obter_filtro(idfiltro, username):
    return get_object_or_404(
        Filtro,
        pk=idfiltro,
        responsavel=username)


def obter_filtros(username):
    return Filtro.objects.filter(
        responsavel=username
    )


@login_required
def filtros(request):
    novo_filtro_form = AdicionarFiltroForm

    return render(
        request,
        'filtro/filtros.html',
        {
            'filtros': obter_filtros(request.user.username),
            'novofiltroform': novo_filtro_form
        }
    )


@login_required
@require_http_methods(['POST'])
def adicionar_filtro(request):
    form = AdicionarFiltroForm(request.POST)
    form.instance.responsavel = request.user.username

    form.save()

    messages.success(request, "Filtro %s adicionado e salvo" % form.instance.nome)

    return redirect(
        reverse(
            'filtros-filtro',
            args=[form.instance.id]
        )
    )


@login_required
def filtro(request, idfiltro):
    m_filtro = obter_filtro(idfiltro, request.user.username)
    form = FiltroForm(instance=m_filtro)

    if request.method == 'POST':
        form = FiltroForm(request.POST, request.FILES, instance=m_filtro)
        form.save()

        messages.success(request, "Filtro salvo!")

    return render(
        request,
        'filtro/filtro.html',
        {
            'form': form,
            'model': m_filtro,
        }
    )


@login_required
@require_http_methods(['POST'])
def excuir_filtro(request):
    idfiltro = request.POST.get('idfiltro')

    m_fitlro = obter_filtro(idfiltro, request.user.username)
    m_fitlro.delete()

    messages.success(request, 'Filtro removido com Sucesso!')
    return redirect(
        reverse(
            'filtros'
        )
    )