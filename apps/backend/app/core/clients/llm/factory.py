from typing import Any
from app.core.clients.llm.providers import OllamaClient
from app.core.clients.llm.client import LLMClient


class LLMClientFactory:
    """
    Instantiate the right client from a plain config dict.

    Config examples:
        {"provider": "ollama",    "model": "llama3"}
        {"provider": "openai",    "model": "gpt-4o"}
        {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022"}
    """

    _registry: dict[str, type[LLMClient]] = {
        "ollama": OllamaClient,
    }

    @classmethod
    def create(cls, config: dict[str, Any]) -> LLMClient:
        provider = config.get("provider", "ollama").lower()
        if provider not in cls._registry:
            raise ValueError(
                f"Unknown provider '{provider}'. Available: {list(cls._registry)}"
            )
        client_cls = cls._registry[provider]
        # Pass model + optional api_key; ignore unknown keys gracefully
        kwargs = {k: v for k, v in config.items() if k != "provider"}
        return client_cls(**kwargs)

    @classmethod
    def register(cls, name: str, client_cls: type[LLMClient]) -> None:
        """Extend with a custom provider at runtime."""
        cls._registry[name] = client_cls
