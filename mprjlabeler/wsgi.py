"""
WSGI config for mprjlabeler project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os
from newrelic.agent import WSGIApplicationWrapper

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mprjlabeler.settings")

application = get_wsgi_application()

application = WSGIApplicationWrapper(application)
