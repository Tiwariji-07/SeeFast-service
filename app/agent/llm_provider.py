"""
LLM Provider Factory
====================

Provides a unified interface for different LLM providers:
- OpenAI (GPT-4, GPT-4o)
- Anthropic (Claude 3.5, Claude 3)
- Google (Gemini 2.0, Gemini 1.5)

Usage:
    from app.agent.llm_provider import get_llm
    llm = get_llm()  # Uses settings.llm_provider
"""

from langchain_core.language_models.chat_models import BaseChatModel
from typing import Literal
from app.config import settings

LLMProvider = Literal["openai", "anthropic", "google"]


def get_llm(provider: LLMProvider = None, model: str = None) -> BaseChatModel:
    """
    Get an LLM instance based on provider.
    
    Args:
        provider: "openai", "anthropic", or "google" (default from settings)
        model: Model name override (default from settings)
    
    Returns:
        LangChain chat model with tool-calling support
    """
    provider = provider or settings.llm_provider
    
    if provider == "openai":
        return _get_openai(model)
    elif provider == "anthropic":
        return _get_anthropic(model)
    elif provider == "google":
        return _get_google(model)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def _get_openai(model: str = None) -> BaseChatModel:
    """Get OpenAI ChatGPT model."""
    from langchain_openai import ChatOpenAI
    
    return ChatOpenAI(
        model=model or settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.1,
    )


def _get_anthropic(model: str = None) -> BaseChatModel:
    """Get Anthropic Claude model."""
    from langchain_anthropic import ChatAnthropic
    
    return ChatAnthropic(
        model=model or settings.anthropic_model,
        api_key=settings.anthropic_api_key,
        temperature=0.1,
    )


def _get_google(model: str = None) -> BaseChatModel:
    """Get Google Gemini model."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    return ChatGoogleGenerativeAI(
        model=model or settings.google_model,
        google_api_key=settings.google_api_key,
        temperature=0.1,
    )


# Model recommendations by use case
MODEL_RECOMMENDATIONS = {
    "fast": {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-haiku-20240307",
        "google": "gemini-2.0-flash",
    },
    "balanced": {
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20241022",
        "google": "gemini-2.0-flash",
    },
    "powerful": {
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20241022",
        "google": "gemini-2.0-pro",
    },
}


def get_available_models() -> dict:
    """Return available models per provider."""
    return {
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307", "claude-3-opus-20240229"],
        "google": ["gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-pro"],
    }
