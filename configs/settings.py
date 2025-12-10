"""
Configuration Management using Environment Variables
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "Smart Travel Recommendation API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017/"
    MONGODB_DB: str = "smart_travel"
    
    # API Security
    API_KEY: Optional[str] = None
    ENABLE_API_KEY_AUTH: bool = False
    
    # BERT Model
    BERT_MODEL_NAME: str = "paraphrase-multilingual-mpnet-base-v2"
    BERT_CACHE_DIR: Optional[str] = None
    
    # Performance
    MAX_PLACES_PER_REQUEST: int = 200
    REQUEST_TIMEOUT_SECONDS: int = 60
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
