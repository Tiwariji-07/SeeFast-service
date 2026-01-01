"""
Application Configuration
=========================

Using Pydantic Settings for configuration management.
Supports .env files and environment variables with layered override.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Provider Selection
    llm_provider: Literal["openai", "anthropic", "google"] = "openai"
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    
    # Anthropic Configuration
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    
    # Google Configuration
    google_api_key: str = ""
    google_model: str = "gemini-2.0-flash"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_ttl: int = 300
    
    # ChromaDB Configuration
    chroma_persist_dir: str = "./chroma_data"
    
    # Swagger Configuration
    swagger_url: str = "https://petstore.swagger.io/v2/swagger.json"
    
    # Embedding Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get settings instance (cached)."""
    return Settings()


settings = get_settings()
