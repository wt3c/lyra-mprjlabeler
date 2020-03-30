"Backends de autenticação customizados"
import base64
import json
import requests
from django.conf import settings
from django.contrib.auth.models import User


class Autenticador:
    "Autenticador para validar usuário no SCA"
    def authenticate(self, request, username, password):
        "Autentica o usuário no SCA, sem revalidar a sessão"
        del request
        password = bytes(password, 'utf-8')
        session = requests.session()
        username = username.strip().lower()

        response = session.post(
            url=settings.AUTH_MPRJ,
            data={
                'username': username,
                'password': base64.b64encode(password).decode("utf-8")
            })
        if response.status_code == 200:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                response = session.get(url=settings.AITJ_MPRJ_USERINFO)
                corpo = json.loads(response.content.decode('utf-8'))
                user = User(username=username)
                user.is_staff = False
                user.is_superuser = False
                user.first_name = ' '.join(
                    corpo['userDetails']['nome'].split()[:2])[:30]
                user.save()
            return user
        return None
