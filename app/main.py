from fastapi import FastAPI
from app.database import engine, Base
from app.api.v1 import workout_router # Apenas para evitar erro de import

# Importa todos os módulos de modelos para garantir que Base.metadata 
# contenha todas as definições de tabela para o Alembic.
from app.models import exercise, log 

# OBS: Não precisamos chamar Base.metadata.create_all(bind=engine) aqui, 
# pois o Alembic fará a gestão da criação das tabelas.

app = FastAPI(title="Gym Tracker API", version="0.0.1")

# 1. Root Endpoint
@app.get("/")
def read_root():
    return {"status": "ok", "message": "API is running"}

# 2. Health Check Endpoint - Phase 1 DoD requirement
@app.get("/ping")
def ping():
    """Health check endpoint to verify API connectivity."""
    return {"status": "ok"}

# A rota de log será adicionada na Fase 2
# app.include_router(workout_router.router, prefix="/api/v1")