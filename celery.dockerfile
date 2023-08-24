FROM python:3.11
LABEL MAINTAINER="Roman Shvietsov"

ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get -y dist-upgrade
RUN apt install -y netcat-traditional

COPY ./requirements.txt /requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r /requirements.txt

RUN mkdir /app
WORKDIR /app
COPY ./app /app

#CMD ["sh", "/scripts/celery_run.sh"]