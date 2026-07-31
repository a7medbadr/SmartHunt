from abc import ABC, abstractmethod

from smarthunt.ai.types import AIRequest, AIResponse


class BaseAIClient(ABC):

    @abstractmethod
    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:
        raise NotImplementedError
