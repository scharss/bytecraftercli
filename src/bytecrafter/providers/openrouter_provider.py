import os
from typing import List, Dict, Any

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None

from .llm_provider import BaseProvider, ProviderNotConfigured


class OpenRouterProvider(BaseProvider):
    """OpenRouter provider (OpenAI-compatible endpoint)."""

    name = "openrouter"

    def _check_configuration(self):
        if openai is None:
            raise ProviderNotConfigured("openai package not installed (needed for OpenRouter)")
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ProviderNotConfigured("OPENROUTER_API_KEY missing")
        openai.api_key = api_key
        openai.api_base = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    def generate(self, history: List[Dict[str, str]], model_name: str | None = None, **kwargs: Any):
        system_instruction = kwargs.pop("system_instruction", None)
        model_name = model_name or os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.extend(history)
        response = openai.ChatCompletion.create(model=model_name, messages=messages, **kwargs)
        return self._wrap(response.choices[0].message.content) 