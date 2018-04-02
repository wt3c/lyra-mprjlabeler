"Case tests para o Labeler"
import json
import os
from httmock import HTTMock, urlmatch
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client

from model_mommy.mommy import make


os.environ['http_proxy'] = ''


@urlmatch(netloc=r'(.*\.)?apps\.mprj\.mp\.br$', method='POST')
def auth_ok(url, request):
    "fixture de autenticacao ok"
    del url, request
    return {
        'status_code': 200,
        'content': '',
    }


@urlmatch(netloc=r'(.*\.)?apps\.mprj\.mp\.br$', method='GET')
def info_auth_ok(url, request):
    "fixture de autenticacao ok"
    del url, request
    return {
        'status_code': 200,
        'content': json.dumps(LOGIN_OK),
    }


LOGIN_OK = {
    "username": "SCAUSER",
    "permissions": {
        "ROLE_Default": True,
        "ROLE_Contracheque": True,
        "ROLE_Public": True
    },
    "userDetails": {
        "orgao": "COORDENADORIA DE ANÁLISES, DIAGNÓSTICOS E GEOPROCESSAMENTO",
        "perfil": "Misto:Servidores->CLASSE,Servidores->CLASSE",
        "login": "JOSENILDO.SILVA",
        "nome": "JOSENILDO DA SILVA"
    }
}


class LoginTestCase(TestCase):
    "Testes do método de login"

    def test_login(self):
        "Login simples"
        cliente = Client()

        with HTTMock(auth_ok, info_auth_ok):
            response = cliente.post(
                '/login/',
                {'usuario': 'lero', 'senha': 'lero'}
            )

        assert response.status_code == 302


class CompletudeCampanha(TestCase):
    """
        Retorna as completudes das campanhas ativas no contexto.
    """
    def test_retorna_completude_de_uma_campanha_ativas(self):
        User = get_user_model()
        usuario = make(User, email='teste@exemplo.com')
        usuario.username = 'teste'
        usuario.set_password('12345')
        usuario.save()
        self.client.login(username='teste', password='12345')

        campanha = make('labeler.Campanha', ativa=True)
        tarefas = make('labeler.Tarefa', _quantity=10, campanha=campanha)
        trabalhos = make('labeler.Trabalho', _quantity=5, tarefas=tarefas)

        # Tres Respostas
        make('labeler.Resposta', tarefa=tarefas[0], trabalho=trabalhos[0])

        resp = self.client.get(reverse('campanhas'))

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'labeler/campanhas.html')
        self.assertEqual(resp.context['completude_geral_campanhas'], [10])
