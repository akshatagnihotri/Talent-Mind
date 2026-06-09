"""
TalentMind AI — Application Configuration
Loads settings from environment variables or .env file via pydantic-settings.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://talentmind:talentmind123@localhost:5432/talentmind"

    # ── Auth / JWT ────────────────────────────────────────────────────────────
    SECRET_KEY: str = "talentmind-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Ollama (local LLM) ────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # ── Feature flags ─────────────────────────────────────────────────────────
    # When DEMO_MODE=true the app returns canned responses instead of calling Ollama.
    DEMO_MODE: bool = False

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # ── File storage ──────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
