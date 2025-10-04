"""
LLM Module - Handles all AI model interactions

Supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Google Gemini (future)
- Local models (future)
"""

from .gemini_client import GoogleClient
from .prompt_templates import PromptTemplates

__all__ = ['OpenAIClient', 'PromptTemplates']

__version__ = '1.0.0'