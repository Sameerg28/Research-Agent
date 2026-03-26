from __future__ import annotations

from abc import ABC, abstractmethod


class LLMInterface(ABC):
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        allow_chunking: bool = False,
    ) -> dict:
        raise NotImplementedError
