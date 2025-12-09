# Environment and config
"""
Centralized configuration management using pydantic-settings.
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "lexivoice"
    
    # API Keys
    GROQ_API_KEY: str
    OPENAI_API_KEY: Optional[str] = None
    
    # Application Settings
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "LexiVoice"
    
    # CORS Settings
    ALLOWED_ORIGINS: list = ["*"]  # Allow all for MVP
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()