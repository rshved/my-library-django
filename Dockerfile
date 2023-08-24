FROM --platform=linux/amd64 python:3.9
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
COPY ./scripts /scripts
COPY ./entrypoint.sh /entrypoint.sh

RUN mkdir /tmp/runtime-user

ENTRYPOINT ["/entrypoint.sh"]
