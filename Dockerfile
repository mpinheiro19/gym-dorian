FROM python:3.11-slim

# Variáveis de ambiente para o driver do Postgres
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instalar dependências do sistema necessárias para compilar psycopg2 (driver do postgres)
RUN apt-get update && apt-get install -y gcc libpq-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY app/ .