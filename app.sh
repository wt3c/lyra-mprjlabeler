#!/bin/bash
if [ -z "$WORKER" ]
then
    # GUNICORN_CMD_ARGS = variável de configuração do Gunicorn
    gunicorn mprjlabeler.wsgi:application --bind=0.0.0.0:8080 --log-file -
else
    celery -A mprjlabeler worker -l info
fi