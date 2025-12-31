"""
Application Configuration
=========================

Using Pydantic Settings for configuration management.
Supports .env files and environment variables with layered override.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_ttl: int = 300  # Cache TTL in seconds (5 minutes)
    
    # ChromaDB Configuration
    chroma_persist_dir: str = "./chroma_data"
    
    # Swagger Configuration
    swagger_url: str = "https://petstore.swagger.io/v2/swagger.json"
    
    # Embedding Configuration
    embedding_model: str = "all-MiniLM-L6-v2"  # Small, fast model
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get settings instance (cached)."""
    return Settings()


settings = get_settings()
