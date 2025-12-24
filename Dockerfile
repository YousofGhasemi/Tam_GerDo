FROM python:3.12-slim
LABEL maintainer="GoYousef.com"

ENV PYTHONUNBUFFERED=1
ENV PATH="/scripts:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        linux-headers-amd64 \
        libpq-dev \
        libjpeg-dev \
        zlib1g \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ../requirements.txt /tmp/requirements.txt
COPY ../requirements.dev.txt /tmp/requirements.dev.txt
COPY ../scripts /scripts
COPY app /app

WORKDIR /app
EXPOSE 8000

RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt

ARG DEV=false
RUN if [ "$DEV" = "true" ] ; then \
        pip install -r /tmp/requirements.dev.txt ; \
    fi

RUN adduser --disabled-password --no-create-home django-user && \
    mkdir -p /vol/web/media /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts

USER django-user
CMD ["run.sh"]
