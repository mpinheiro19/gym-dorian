from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # O valor padrão é o que será usado se a variável não for setada, 
    # mas o docker-compose garante que ela será setada.
    DATABASE_URL: str = "postgresql+psycopg2://user:password@localhost:5432/gym_db"
    
    # Exemplo de configuração adicional
    ENV_STATE: str = "development"
    
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

settings = Settings()