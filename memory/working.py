from __future__ import annotations

from interfaces.memory import MemoryInterface


class WorkingMemory(MemoryInterface):
    def __init__(self, backend: MemoryInterface) -> None:
        self._backend = backend

    def store(self, key: str, data: object) -> None:
        self._backend.store(key, data)

    def retrieve(self, key: str, default: object | None = None) -> object | None:
        return self._backend.retrieve(key, default)

    def update(self, key: str, data: object) -> None:
        self._backend.update(key, data)

    def remember(self, note: str) -> None:
        self._backend.remember(note)

    def record_tool_result(self, tool_name: str, summary: str) -> None:
        self._backend.record_tool_result(tool_name, summary)

    def add_queries(self, queries: list[dict[str, str]]) -> list[dict[str, str]]:
        return self._backend.add_queries(queries)

    def add_insights(self, insights: list[str], minimum_quality: float = 0.35) -> list[str]:
        return self._backend.add_insights(insights, minimum_quality=minimum_quality)

    def add_follow_up_questions(self, questions: list[str]) -> list[str]:
        return self._backend.add_follow_up_questions(questions)

    def add_sources(self, sources: list[dict[str, str]]) -> list[dict[str, str]]:
        return self._backend.add_sources(sources)

    def snapshot(self, max_chars: int = 4000) -> str:
        return self._backend.snapshot(max_chars=max_chars)

    def export_deep_research(
        self,
        breadth_used: int,
        depth_requested: int,
        depth_completed: int,
    ) -> dict:
        return self._backend.export_deep_research(
            breadth_used=breadth_used,
            depth_requested=depth_requested,
            depth_completed=depth_completed,
        )
