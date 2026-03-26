from __future__ import annotations

from abc import ABC, abstractmethod


class SearchInterface(ABC):
    @abstractmethod
    def search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        raise NotImplementedError
