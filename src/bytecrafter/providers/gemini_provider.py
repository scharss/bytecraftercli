import os
from typing import List, Dict, Any
import google.generativeai as genai

from .llm_provider import BaseProvider, ProviderNotConfigured


class GeminiProvider(BaseProvider):
    name = "gemini"

    def _check_configuration(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ProviderNotConfigured("GEMINI_API_KEY missing")
        genai.configure(api_key=api_key)

    def generate(self, history: List[Dict[str, str]], model_name: str | None = None, **kwargs: Any):
        system_instruction = kwargs.pop("system_instruction", None)
        model_name = model_name or os.getenv("DEFAULT_GEMINI_MODEL", "gemini-1.5-flash")
        if system_instruction:
            model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)
        else:
            model = genai.GenerativeModel(model_name=model_name)
        raw = model.generate_content(history, **kwargs)
        text = raw.candidates[0].content.parts[0].text
        return self._wrap(text) 