from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as django_login
from .backends import Autenticador
from .models import Campanha, Resposta

from django import forms


@login_required
def campanhas(request):
    campanhas = Campanha.objects.filter(ativa=True)
    return render(request, 'labeler/campanhas.html', {'campanhas': campanhas})


@login_required
def campanha(request, idcampanha):
    campanha = get_object_or_404(Campanha, id=idcampanha)

    tarefa = campanha.obter_tarefa(request.user.username)

    if not tarefa:
        return render(request, 'labeler/finalizado.html', {'campanha': campanha})
    
    form = RespostaForm(campos=campanha.formulario.estrutura['campos'])
    
    if request.method == 'POST':
        form = RespostaForm(request.POST, campos=campanha.formulario.estrutura['campos'])
        form.is_valid()

        for campo in form.fields:
            resposta = Resposta()
            resposta.username = request.user.username
            resposta.tarefa = tarefa
            resposta.nomecampo = campo
            resposta.valor = str(form.cleaned_data[campo])
            resposta.save()
        
        tarefa = campanha.obter_tarefa(request.user.username)
        form = RespostaForm(campos=campanha.formulario.estrutura['campos'])

    return render(
        request,
        'labeler/pergunta.html', {
            'campanha': campanha,
            'tarefa': tarefa,
            'form': form
        })


def login(request):
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


class RespostaForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'campos' not in kwargs:
            raise Exception(
                '"campos" não foi fornecido para a criação do form')

        campos = kwargs.pop('campos')
        super(RespostaForm, self).__init__(*args, **kwargs)

        for campo in campos:
            if 'escolha' in campo:
                campo = campo['escolha']
                opcoes = campo['opcoes']
                valores = campo['valores']
                nome = campo['nome']
                label = campo['label']
                if 'obrigatorio' in campo:
                    obrigatorio = campo['obrigatorio']


                if campo['cardinalidade'] == 'multipla':
                    tipo_campo = forms.MultipleChoiceField
                else:
                    tipo_campo = forms.ChoiceField

                field = tipo_campo(choices=zip(valores, opcoes), label=label, required=obrigatorio)

                self.fields[nome] = field

            if 'check' in campo:
                campo = campo['check']
                nome = campo['nome']
                label = campo['label']
                default = campo['default']

                field = forms.BooleanField(label=label, initial=default, required=False)

                self.fields[nome] = field

