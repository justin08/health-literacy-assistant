import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    jwt_secret: str = "dev-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # leave blank to run without llm (falls back to keyword matching)
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-nano"

    # LLM settings
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1024

    chroma_persist_dir: str = "./chroma_data"
    data_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    cors_origins: str = "http://localhost:8501,http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
