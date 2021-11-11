FROM python:3.9.7-alpine3.14

COPY pyproject.toml /

RUN apk add \
        libffi-dev \
        musl-dev \
        gcc && \
    pip install --upgrade pip && \
    pip install poetry==1.1.11 && \
    poetry config virtualenvs.create false --local && \
    poetry install

COPY . /app
WORKDIR /app
