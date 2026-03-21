from app.core.clients.llm.models import LLMResponse, Message, Role
from typing import Protocol, Any


class LLMClient(Protocol):
    def complete(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> LLMResponse: ...

    def complete_simple(self, prompt: str, system: str | None = None, **kwargs) -> str:
        """Convenience wrapper — skips building Message objects manually."""
        messages = []
        if system:
            messages.append(Message(role=Role.SYSTEM, content=system))
        messages.append(Message(role=Role.USER, content=prompt))
        return self.complete(messages, **kwargs).content
