from enum import StrEnum
from dataclasses import dataclass, field


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTENT = "assistant"


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    # {"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200}


@dataclass
class Message:
    role: Role
    content: str
