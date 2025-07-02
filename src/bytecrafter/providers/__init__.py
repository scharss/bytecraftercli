import os
from importlib import import_module

from .llm_provider import BaseProvider, ProviderNotConfigured

# Registro de proveedores soportados
_PROVIDER_CLASSES = {
    "gemini": "bytecrafter.providers.gemini_provider.GeminiProvider",
    "openai": "bytecrafter.providers.openai_provider.OpenAIProvider",
    "groq": "bytecrafter.providers.groq_provider.GroqProvider",
    "openrouter": "bytecrafter.providers.openrouter_provider.OpenRouterProvider",
    "ollama": "bytecrafter.providers.ollama_provider.OllamaProvider",
    # Placeholders for future providers
    "vertex": "bytecrafter.providers.stub_provider.StubProvider",
    "deepseek": "bytecrafter.providers.deepseek_provider.DeepSeekProvider",
    "mistral": "bytecrafter.providers.mistral_provider.MistralProvider",
    "xai": "bytecrafter.providers.xai_provider.XAIProvider",
}


def _load_class(path: str):
    module_name, class_name = path.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, class_name)


def _auto_select() -> BaseProvider:
    preferred = os.getenv("PREFERRED_LLM_PROVIDER", "auto").lower()

    def instantiate(name: str):
        path = _PROVIDER_CLASSES.get(name)
        if not path:
            return None
        cls = _load_class(path)
        try:
            return cls()
        except ProviderNotConfigured:
            return None

    if preferred != "auto":
        provider = instantiate(preferred)
        if provider:
            return provider

    # Fallback: iterate in declared order
    for key in [
        "gemini",
        "openai",
        "groq",
        "openrouter",
        "deepseek",
        "mistral",
        "ollama",
        "vertex",
        "xai",
    ]:
        provider = instantiate(key)
        if provider:
            return provider
    raise RuntimeError("No configured LLM provider found in environment variables.")


current_provider: BaseProvider = _auto_select() 