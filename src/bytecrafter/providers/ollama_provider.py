import os
from typing import List, Dict, Any
import requests

from .llm_provider import BaseProvider, ProviderNotConfigured


class OllamaProvider(BaseProvider):
    name = "ollama"

    def _check_configuration(self):
        # No API key required, just base URL reachability check (optional)
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._url = base_url.rstrip("/")
        # Optionally verify server is up
        try:
            requests.get(f"{self._url}/")
        except Exception as exc:  # pragma: no cover
            raise ProviderNotConfigured(f"Cannot connect to Ollama at {self._url}: {exc}")

    def generate(self, history: List[Dict[str, str]], model_name: str | None = None, **kwargs: Any):
        system_instruction = kwargs.pop("system_instruction", None)
        model_name = model_name or os.getenv("OLLAMA_MODEL", "llama3:8b")
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.extend(history)

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
        }
        timeout = int(os.getenv("OLLAMA_TIMEOUT", "300"))
        resp = requests.post(f"{self._url}/api/chat", json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return self._wrap(data.get("message", {}).get("content", "")) 