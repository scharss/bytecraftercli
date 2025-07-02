import os
from typing import List, Dict, Any
import requests

from .llm_provider import BaseProvider, ProviderNotConfigured


class DeepSeekProvider(BaseProvider):
    name = "deepseek"

    def _check_configuration(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ProviderNotConfigured("DEEPSEEK_API_KEY missing")
        self._api_key = api_key
        self._base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

    def _chat(self, model: str, messages: List[Dict[str, str]], **kwargs):
        url = f"{self._base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        payload.update(kwargs)
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def generate(self, history: List[Dict[str, str]], model_name: str | None = None, **kwargs: Any):
        system_instruction = kwargs.pop("system_instruction", None)
        model_name = model_name or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.extend(history)
        data = self._chat(model=model_name, messages=messages, **kwargs)
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return self._wrap(text) 