FROM python:3.9

RUN mkdir /usr/src/app
WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

RUN pip install -U pip && \
    pip install poetry

COPY pyproject.toml poetry.lock /usr/src/app/

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi --only main

COPY . /usr/src/app/
