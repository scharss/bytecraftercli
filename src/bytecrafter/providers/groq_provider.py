import os
from typing import List, Dict, Any

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None

from .llm_provider import BaseProvider, ProviderNotConfigured


class GroqProvider(BaseProvider):
    name = "groq"

    def _check_configuration(self):
        if openai is None:
            raise ProviderNotConfigured("openai package not installed (needed for Groq)")
        api_key = os.getenv("GROQ_API_KEY")
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        if not api_key:
            raise ProviderNotConfigured("GROQ_API_KEY missing")
        openai.api_key = api_key
        openai.api_base = base_url

    def generate(self, history: List[Dict[str, str]], model_name: str | None = None, **kwargs: Any):
        system_instruction = kwargs.pop("system_instruction", None)
        model_name = model_name or os.getenv("GROQ_MODEL", "llama3-70b-8192")
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.extend(history)
        response = openai.ChatCompletion.create(model=model_name, messages=messages, **kwargs)
        return self._wrap(response.choices[0].message.content) 