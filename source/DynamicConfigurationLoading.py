from pydantic_settings import BaseSettings

class TGConfig(BaseSettings):
    LOG_LEVEL: str = "INFO"

    RAG_HOST: str = "localhost"
    RAG_PORT: int = 8080
    RAG_N_RESULT: int = 5
    SENTENCE_TRANSFORMER_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    MISTRAL_API_KEY: str = ""
    MISTRAL_API_MODEL: str = "mistral-7b"

    PYRO_API_ID: str = ""
    PYRO_API_HASH: str = ""
    PYRO_HISTORY_LIMIT: int = 100

    # PostgreSQL Configuration (вместо MongoDB)
    POSTGRES_USER: str = "telerag_user"
    POSTGRES_PASSWORD: str = "telerag_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "telerag_db"

    AIOGRAM_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_config() -> TGConfig:
    stn = TGConfig()
    print(stn.__dict__)
    return stn