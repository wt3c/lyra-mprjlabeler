FROM python:3.7

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get -yq install build-essential libyaml-dev
RUN apt-get clean

WORKDIR /app

COPY . /app

RUN mkdir -p /media

RUN pip install -r requirements.txt

RUN python manage.py collectstatic --noinput

VOLUME ["/media"]
