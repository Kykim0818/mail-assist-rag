from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# .env is at project root (one level up from backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


class Settings(BaseSettings):
    GITHUB_TOKEN: str = "your_github_token_here"
    MODEL_NAME: str = "openai/gpt-5-mini"
    EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    DB_PATH: str = "mail_assistant.db"
    CHROMA_PATH: str = "chroma_data"


settings = Settings()
