import os
from typing import List, Dict, Any

try:
    import openai
except ImportError:  # pragma: no cover
    openai = None

from .llm_provider import BaseProvider, ProviderNotConfigured


class OpenAIProvider(BaseProvider):
    name = "openai"

    def _check_configuration(self):
        if openai is None:
            raise ProviderNotConfigured("openai package not installed")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ProviderNotConfigured("OPENAI_API_KEY missing")
        openai.api_key = api_key
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")
        if base_url:
            openai.api_base = base_url

    def generate(self, history: List[Dict[str, str]], model_name: str | None = None, **kwargs: Any):
        system_instruction = kwargs.pop("system_instruction", None)
        model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.extend(history)
        response = openai.ChatCompletion.create(model=model_name, messages=messages, **kwargs)
        return self._wrap(response.choices[0].message.content) 