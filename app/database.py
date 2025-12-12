from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings
# A base será importada do models para evitar dependência circular
from models.base import Base # Será implementado no próximo passo

# engine (Pool de conexões)
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True
)

# Sessão local para injeção de dependência
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependência para endpoints da FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()