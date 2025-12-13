# Gym Dorian — Backend API

Projeto backend minimalista para acompanhar treinos (exercícios, sessões e logs),
construído com FastAPI e SQLAlchemy, com migrações gerenciadas pelo Alembic.

**Resumo rápido**
- **API**: FastAPI
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **DB**: PostgreSQL (via Docker)

**Conteúdo deste README**
- **Instalação** e execução com Docker Compose
- Como rodar localmente sem Docker
- Uso do Alembic (gerar e aplicar migrações)
- Estrutura principal do projeto

**Requisitos**
- Docker & Docker Compose (recomendado)
- Python 3.11 (opcional para execução local)

**Executando com Docker (recomendado)**

1. Subir serviços:

```bash
docker-compose up --build -d
```

2. Verificar logs da API:

```bash
docker logs -f gym_tracker_api
```

3. API disponível em `http://localhost:8000/` (endpoint de saúde) e documentação em `http://localhost:8000/docs`.

**Migrações (Alembic)**

Os arquivos de configuração do Alembic estão na raiz (`alembic.ini`) e no diretório `alembic/`.
Exemplos de comandos (executados dentro do container da API):

```bash
# Gerar uma nova migration (autogenerate)
docker exec -it gym_tracker_api sh -c "cd / && alembic revision --autogenerate -m 'Mensagem'"

# Aplicar migrações
docker exec -it gym_tracker_api sh -c "cd / && alembic upgrade head"

# Ver estado atual
docker exec -it gym_tracker_api sh -c "cd / && alembic current"
```

Observações:
- O projeto já inclui um exemplo de migração inicial (tabelas `exercises`, `workout_sessions`, `log_exercises`).
- Se alterar a estrutura de módulos / imports, verifique `alembic/env.py` para garantir que o `target_metadata` aponte para `models.Base`.

**Rodando localmente (sem Docker)**

1. Criar venv e ativar:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instalar dependências (arquivo de exemplo em `gym_tracker_api/requirements.txt`):

```bash
pip install -r gym_tracker_api/requirements.txt
```

3. Ajustar variável de ambiente `DATABASE_URL` (ex.: conectar em um Postgres local).

4. Executar a API (na raiz do projeto, já que o código está em `app/` e o `Dockerfile` usa `/app` como workdir):

```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Configuração do Banco de Dados**

A aplicação utiliza Pydantic Settings para gerenciar configurações através de variáveis de ambiente.

Variáveis de ambiente disponíveis:

- **`DATABASE_URL`** (obrigatória): URL de conexão PostgreSQL
  - Formato: `postgresql+psycopg2://user:password@host:port/database`
  - Docker Compose: Automaticamente configurado como `postgresql+psycopg2://user:password@db:5432/gym_db`
  - Local: Configure manualmente ou via arquivo `.env`
  
- **`ENV_STATE`** (opcional): Estado do ambiente da aplicação
  - Valores aceitos: `development` (padrão), `staging`, `production`
  - Docker Compose: Automaticamente configurado conforme necessário

**Ordem de prioridade de configuração:**
1. Variáveis de ambiente do sistema (usadas pelo Docker Compose) — prioridade máxima
2. Arquivo `.env` na raiz do projeto — fallback para desenvolvimento local
3. Valores padrão no código — última opção

**Exemplo de arquivo `.env` para desenvolvimento local:**

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/gym_db
ENV_STATE=development
```

**Validação:**
- `DATABASE_URL` deve ser uma URL PostgreSQL válida (validada pelo Pydantic)
- `ENV_STATE` aceita apenas: `development`, `staging`, ou `production`
- Configurações extras são ignoradas automaticamente

**Estrutura do projeto**

- `app/` — código da aplicação (rotas, modelos, serviços)
	- `api/` — roteadores (ex.: `v1/workout_router.py`)
	- `core/` — configurações (Pydantic Settings)
	- `models/` — modelos SQLAlchemy (`exercise.py`, `log.py`, `plan.py`)
	- `schemas/` — Pydantic schemas
	- `services/` — lógica de negócio
	- `main.py`, `database.py`
- `alembic/` — scripts de migração e template (`env.py`, `script.py.mako`)
- `alembic.ini` — configuração do Alembic
- `docker-compose.yml`, `Dockerfile` — configuração e imagem da API