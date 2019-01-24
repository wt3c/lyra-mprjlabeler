from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from .forms import (
    AdicionarFiltroForm,
    FiltroForm,
    AdicionarClasseForm,
    ItemFiltroForm,
)
from .models import (
    Filtro,
    ClasseFiltro,
    ItemFiltro
)
from .tasks import submeter_classificacao


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

    messages.success(
        request,
        "Filtro %s adicionado e salvo" % form.instance.nome)

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
        form = FiltroForm(
            request.POST,
            request.FILES,
            instance=m_filtro
        )
        form.is_valid()
        form.save()

        messages.success(request, "Filtro salvo!")

    return render(
        request,
        'filtro/filtro.html',
        {
            'form': form,
            'model': m_filtro,
            'idfiltro': idfiltro,
            'adicionarclasseform': AdicionarClasseForm(),
            'itemfiltroform': ItemFiltroForm(),
        }
    )


@login_required
@require_http_methods(['POST'])
def excuir_filtro(request):
    idfiltro = request.POST.get('idfiltro')

    m_filtro = obter_filtro(idfiltro, request.user.username)
    m_filtro.delete()

    messages.success(request, 'Filtro removido com Sucesso!')
    return redirect(
        reverse(
            'filtros',
        )
    )


@login_required
@require_http_methods(['POST'])
def adicionar_classe(request, idfiltro):
    f_adicionar = AdicionarClasseForm(request.POST)

    if not f_adicionar.is_valid():
        return None

    if f_adicionar.cleaned_data['idclasse']:
        f_adicionar = AdicionarClasseForm(
            request.POST,
            instance=get_object_or_404(
                ClasseFiltro,
                pk=f_adicionar.cleaned_data['idclasse'])
        )

        f_adicionar.save()
        messages.success(request, 'Classe de Filtro alterada com sucesso!')
    else:
        m_filtro = obter_filtro(idfiltro, request.user.username)

        f_adicionar.instance.filtro = m_filtro
        f_adicionar.instance.ordem = len(m_filtro.classefiltro_set.all())
        f_adicionar.save()

        messages.success(request, 'Classe de Filtro adicionada!')

    return redirect(
        reverse(
            'filtros-filtro',
            args=[idfiltro]
        )
    )


@login_required
@require_http_methods(['POST'])
def excluir_classe(request, idfiltro, idclasse):
    m_classe = get_object_or_404(
        ClasseFiltro,
        pk=idclasse,
        filtro__id=idfiltro
    )

    m_classe.delete()

    messages.warning(request, 'Classe de filtro removida')

    return redirect(
            reverse(
                'filtros-filtro',
                args=[idfiltro]
            )
        )


@login_required
@require_http_methods(['GET'])
def mover_classe(request, idfiltro, idclasse, direcao):
    m_classe = get_object_or_404(
        ClasseFiltro,
        pk=idclasse,
        filtro__id=idfiltro)

    if direcao == 'acima':
        m_classe.up()

    else:
        m_classe.down()

    messages.success(request, 'Classe movida %s!' % direcao)

    return redirect(
        reverse(
            'filtros-filtro',
            args=[idfiltro]
        )
    )


@login_required
@require_http_methods(['POST'])
def adicionar_itemfiltro(request):
    f_itemfiltro = ItemFiltroForm(request.POST)

    if f_itemfiltro.is_valid():
        if f_itemfiltro.cleaned_data['iditemfiltro']:
            m_itemfiltro = get_object_or_404(
                ItemFiltro,
                pk=f_itemfiltro.cleaned_data['iditemfiltro']
            )

            f_itemfiltro = ItemFiltroForm(
                request.POST,
                instance=m_itemfiltro)

            f_itemfiltro.save()

            messages.success(request, 'Item de Filtro alterado!')
        else:
            f_itemfiltro.instance.classe_filtro = get_object_or_404(
                ClasseFiltro,
                pk=f_itemfiltro.cleaned_data['idclasse'])

            f_itemfiltro.save()

            messages.success(request, 'Item de Filtro adicionado!')

    return redirect(
        reverse(
            'filtros-filtro',
            args=[f_itemfiltro.cleaned_data['idfiltro']]
        )
    )


@login_required
@require_http_methods(['GET'])
def excluir_item_filtro(request, idfiltro, iditemfiltro):
    m_itemfiltro = get_object_or_404(ItemFiltro, pk=iditemfiltro)

    m_itemfiltro.delete()

    messages.warning(request, 'Item de Filtro removido com sucesso!')

    return redirect(
        reverse(
            'filtros-filtro',
            args=[idfiltro]
        )
    )


@login_required
@require_http_methods(['GET'])
def classificar(request, idfiltro):
    m_filtro = obter_filtro(idfiltro, request.user.username)

    submeter_classificacao.delay(idfiltro)

    m_filtro.situacao = '2'
    m_filtro.save()

    messages.info(request, 'Filtro submetido para classificação! Acompanhe o andamento pela tela de gestão dos filtros.')

    return redirect(
        reverse(
            'filtros-filtro',
            args=[idfiltro]
        )
    )
