#!/bin/bash
# GUNICORN_CMD_ARGS = variável de configuração do Gunicorn
gunicorn mprjlabeler.wsgi:application --log-file -