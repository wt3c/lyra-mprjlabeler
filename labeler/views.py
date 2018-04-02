"Web Views do módulo Labeler"
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as django_login
from .backends import Autenticador
from .models import Campanha
from .forms import RespostaForm


@login_required
def campanhas(request):
    "View para retornar lista de Campanhas"
    campanhas_ativas = Campanha.objects.filter(ativa=True)
    completude_campanhas = [camp.obter_completude_geral() for
                            camp in campanhas_ativas]
    contexto = {
        'campanhas': campanhas_ativas,
        'completude_geral_campanhas': completude_campanhas
    }
    return render(
        request,
        'labeler/campanhas.html',
        contexto)


@login_required
def campanha(request, idcampanha, pedirnovo=False):
    "Tela para responder tarefas de campanha"
    campanha_ativa = get_object_or_404(Campanha, id=idcampanha)

    form = RespostaForm(campos=campanha_ativa.formulario.estrutura['campos'])

    tarefa = campanha_ativa.obter_tarefa(request.user.username, pedirnovo)

    if request.method == 'POST':
        form = RespostaForm(
            request.POST,
            campos=campanha_ativa.formulario.estrutura['campos'])
        form.is_valid()

        respostas = []

        for campo in form.fields:
            respostas += [{
                'nomecampo': campo,
                'resposta': str(form.cleaned_data[campo])
            }]

        tarefa.votar(request.user.username, respostas)

        tarefa = campanha_ativa.obter_tarefa(request.user.username)
        form = RespostaForm(
            campos=campanha_ativa.formulario.estrutura['campos'])

    if not tarefa:
        return render(
            request,
            'labeler/finalizado.html',
            {'campanha': campanha_ativa})

    return render(
        request,
        'labeler/pergunta.html', {
            'campanha': campanha_ativa,
            'tarefa': tarefa,
            'form': form
        })


def login(request):
    "Tela de login"
    status = 200

    if request.method == 'POST':
        usuario = Autenticador().authenticate(request,
                                              request.POST.get('username', ''),
                                              request.POST.get('password', ''))

        if usuario:
            django_login(request, usuario)
            return redirect('campanhas')
        else:
            messages.add_message(request, messages.ERROR,
                                 'Usuário ou Senha inválidos')
            status = 403

    return render(request, 'labeler/login.html', status=status)
