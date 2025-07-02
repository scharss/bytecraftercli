from .llm_provider import BaseProvider, ProviderNotConfigured


class StubProvider(BaseProvider):
    name = "stub"

    def _check_configuration(self):
        raise ProviderNotConfigured("Provider not implemented yet")

    def generate(self, *args, **kwargs):
        raise ProviderNotConfigured("Provider not implemented yet") 