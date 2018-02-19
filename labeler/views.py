"Web Views do módulo Labeler"
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as django_login
from .backends import Autenticador
from .models import Campanha, Resposta
from .forms import RespostaForm


@login_required
def campanhas(request):
    "View para retornar lista de Campanhas"
    campanhas_ativas = Campanha.objects.filter(ativa=True)
    return render(
        request,
        'labeler/campanhas.html',
        {'campanhas': campanhas_ativas})


@login_required
def campanha(request, idcampanha):
    "Tela para responder tarefas de campanha"
    campanha_ativa = get_object_or_404(Campanha, id=idcampanha)

    tarefa = campanha_ativa.obter_tarefa(request.user.username)

    if not tarefa:
        return render(
            request,
            'labeler/finalizado.html',
            {'campanha': campanha_ativa})

    form = RespostaForm(campos=campanha_ativa.formulario.estrutura['campos'])

    if request.method == 'POST':
        form = RespostaForm(
            request.POST,
            campos=campanha_ativa.formulario.estrutura['campos'])
        form.is_valid()

        for campo in form.fields:
            resposta = Resposta()
            resposta.username = request.user.username
            resposta.tarefa = tarefa
            resposta.nomecampo = campo
            resposta.valor = str(form.cleaned_data[campo])
            resposta.save()

        tarefa = campanha_ativa.obter_tarefa(request.user.username)
        form = RespostaForm(
            campos=campanha_ativa.formulario.estrutura['campos'])

    return render(
        request,
        'labeler/pergunta.html', {
            'campanha': campanha_ativa,
            'tarefa': tarefa,
            'form': form
        })


def login(request):
    "Tela de login"
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

    return render(request, 'labeler/login.html')
