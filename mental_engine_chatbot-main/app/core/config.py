import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT NAME", "Mental Engine Chatbot")
    THREAD_ID: str = os.getenv("THREAD_ID", "abc345")  # should be made dynamic
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    class Config:
        env_file = ".env"


settings = Settings()
