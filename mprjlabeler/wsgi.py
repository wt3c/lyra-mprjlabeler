"""
WSGI config for mprjlabeler project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os
import newrelic.agent
from django.core.wsgi import get_wsgi_application


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

newrelic.agent.initialize(os.path.join(BASE_DIR, 'newrelic.ini'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mprjlabeler.settings")

application = get_wsgi_application()

application = newrelic.agent.WSGIApplicationWrapper(application)
