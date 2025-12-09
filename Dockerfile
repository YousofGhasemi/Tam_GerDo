FROM python:3.12-slim
LABEL maintainer="GoYousef.com"

ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt

ARG DEV=false
RUN if [ "$DEV" = "true" ] ; then \
        pip install -r /tmp/requirements.dev.txt ; \
    fi

RUN adduser --disabled-password --gecos "" django-user
USER django-user
