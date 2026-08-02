from enum import Enum

from pydantic import BaseModel, Field


class AIProvider(str, Enum):
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    LOCAL = "local"


class AIRequest(BaseModel):

    prompt: str = Field(
        min_length=1,
    )

    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
    )

    max_tokens: int = Field(
        # 2048 on the real local Ollama provider (a small CPU-bound
        # model, see settings.ollama_model) reliably took 60-90+s to
        # generate — well past the old 30s timeout below, so every
        # untuned caller (e.g. the AI Assistant chat) silently timed
        # out on every real attempt and fell back to the fake
        # "[LOCAL LLM] {prompt}" echo stub instead of a real answer.
        default=512,
        ge=1,
    )

    timeout: float = Field(
        default=90.0,
        gt=0,
    )

    provider: AIProvider | None = None


class AIResponse(BaseModel):

    content: str

    provider: AIProvider

    success: bool = True

    error: str | None = None


class AIProviderHealth(BaseModel):

    provider: AIProvider

    available: bool = True

    message: str | None = None
