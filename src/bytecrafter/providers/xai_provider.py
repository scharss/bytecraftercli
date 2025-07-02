import os
from typing import List, Dict, Any

try:
    import openai
except ImportError:
    openai = None

from .llm_provider import BaseProvider, ProviderNotConfigured


class XAIProvider(BaseProvider):
    name = "xai"

    def _check_configuration(self):
        if openai is None:
            raise ProviderNotConfigured("openai package not installed (needed for xAI)")
        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            raise ProviderNotConfigured("XAI_API_KEY missing")
        openai.api_key = api_key
        openai.api_base = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")

    def generate(self, history: List[Dict[str, str]], model_name: str | None = None, **kwargs: Any):
        system_instruction = kwargs.pop("system_instruction", None)
        model_name = model_name or os.getenv("XAI_MODEL", "grok-1")
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.extend(history)
        resp = openai.ChatCompletion.create(model=model_name, messages=messages, **kwargs)
        return self._wrap(resp.choices[0].message.content) 