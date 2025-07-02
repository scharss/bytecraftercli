import os
from typing import List, Dict, Any

try:
    from mistralai.client import MistralClient
except ImportError:  # pragma: no cover
    MistralClient = None

from .llm_provider import BaseProvider, ProviderNotConfigured


class MistralProvider(BaseProvider):
    """Provider for Mistral AI platform."""

    name = "mistral"

    def _check_configuration(self):
        if MistralClient is None:
            raise ProviderNotConfigured("mistralai package not installed")
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ProviderNotConfigured("MISTRAL_API_KEY missing")
        self._client = MistralClient(api_key=api_key)

    def generate(self, history: List[Dict[str, str]], model_name: str | None = None, **kwargs: Any):
        system_instruction = kwargs.pop("system_instruction", None)
        model_name = model_name or os.getenv("MISTRAL_MODEL", "mistral-small-latest")
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.extend(history)
        resp = self._client.chat(model=model_name, messages=messages)
        return self._wrap(resp.choices[0].message.content) 