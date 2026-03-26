from __future__ import annotations

from abc import ABC, abstractmethod


class MemoryInterface(ABC):
    @abstractmethod
    def store(self, key: str, data: object) -> None:
        raise NotImplementedError

    @abstractmethod
    def retrieve(self, key: str, default: object | None = None) -> object | None:
        raise NotImplementedError

    @abstractmethod
    def update(self, key: str, data: object) -> None:
        raise NotImplementedError

    @abstractmethod
    def remember(self, note: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def record_tool_result(self, tool_name: str, summary: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_queries(self, queries: list[dict[str, str]]) -> list[dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def add_insights(self, insights: list[str], minimum_quality: float = 0.35) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def add_follow_up_questions(self, questions: list[str]) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def add_sources(self, sources: list[dict[str, str]]) -> list[dict[str, str]]:
        raise NotImplementedError

    @abstractmethod
    def snapshot(self, max_chars: int = 4000) -> str:
        raise NotImplementedError

    @abstractmethod
    def export_deep_research(
        self,
        breadth_used: int,
        depth_requested: int,
        depth_completed: int,
    ) -> dict:
        raise NotImplementedError
