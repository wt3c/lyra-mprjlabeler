"Case tests para o Labeler"
import json
import os
from httmock import HTTMock, urlmatch
from django.test import TestCase, Client

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
