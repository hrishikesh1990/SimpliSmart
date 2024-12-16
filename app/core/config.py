from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cluster Management API"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration
    POSTGRES_SERVER: str = os.getenv("PGHOST", "localhost")
    POSTGRES_USER: str = os.getenv("PGUSER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("PGPASSWORD", "")
    POSTGRES_DB: str = os.getenv("PGDATABASE", "cluster_management")
    POSTGRES_PORT: str = os.getenv("PGPORT", "5432")
    
    # JWT configuration
    SECRET_KEY: str = "TODO_CHANGE_THIS_SECRET_KEY"  # TODO: Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

settings = Settings()
