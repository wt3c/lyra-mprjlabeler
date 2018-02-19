import requests
import base64
import json
from django.conf import settings
from django.contrib.auth.models import User

class Autenticador:
    def authenticate(self, request, username, password):
        password = bytes(password, 'utf-8')
        session = requests.session()
        response = session.post(url=settings.AUTH_MPRJ,
                                 data={
                                     'username': username,
                                     'password': base64.b64encode(password).decode("utf-8")
                                 })
        if response.status_code == 200:
            try:
               user = User.objects.get(username=username)
            except:
                response = session.get(url=settings.AITJ_MPRJ_USERINFO)
                corpo = json.loads(response.content.decode('utf-8'))
                user = User(username=username)
                user.is_staff = False
                user.is_superuser = False
                user.first_name = corpo['userDetails']['nome']
                user.save()
            return user
        return None
