FROM python:3.11-slim

# Variáveis de ambiente para o driver do Postgres
ENV PYTHONUNBUFFERED 1

# Set the working directory to /app (parent of app/ code directory)
WORKDIR /code

# Instalar dependências do sistema necessárias para compilar psycopg2 (driver do postgres)
RUN apt-get update && apt-get install -y gcc libpq-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação mantendo a estrutura app/
COPY app/ /code/app/

# Set PYTHONPATH so Python can find the app module
ENV PYTHONPATH=/code