# syntax=docker/dockerfile:1

FROM python:latest

WORKDIR /app

COPY . .

RUN pip install --upgrade pip poetry && poetry install

ENTRYPOINT ["ahmia"]
