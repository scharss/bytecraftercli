from __future__ import annotations

from typing import List, Dict, Any


class ProviderNotConfigured(Exception):
    """Raised when the required environment variables/SDK for a provider are missing."""


class BaseProvider:
    """Base class for LLM providers."""

    name: str = "base"

    def __init__(self):
        self._check_configuration()

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def generate(self, history: List[Dict[str, str]], model_name: str | None = None, **kwargs: Any):
        """Generate a response from the model.

        `history` follows OpenAI-like format: list of {"role": "user|assistant|system", "content": str}.
        Must return a dict with at least `content: str` field.
        """
        raise NotImplementedError

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    def _check_configuration(self):
        """Validate that the provider can run. Should raise ProviderNotConfigured if not."""
        pass

    # ---------------------------------------------------------------------
    # Helper to standardise output
    # ---------------------------------------------------------------------
    @staticmethod
    def _wrap(text: str) -> Dict[str, str]:
        """Return response in normalised format."""
        return {"content": text} 