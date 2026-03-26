from __future__ import annotations

import re

from interfaces.memory import MemoryInterface


class SimpleMemory(MemoryInterface):
    def __init__(self) -> None:
        self._data: dict[str, object] = {
            "notes": [],
            "tool_results": [],
            "generated_queries": [],
            "insights": [],
            "follow_up_questions": [],
            "visited_sources": [],
            "best_score": 0.0,
        }

    def store(self, key: str, data: object) -> None:
        self._data[key] = data

    def retrieve(self, key: str, default: object | None = None) -> object | None:
        return self._data.get(key, default)

    def update(self, key: str, data: object) -> None:
        self._data[key] = data

    def remember(self, note: str) -> None:
        note = " ".join(note.split())
        if not note:
            return
        notes = list(self.retrieve("notes", []))
        if note not in notes:
            notes.append(note)
        self.update("notes", notes)

    def record_tool_result(self, tool_name: str, summary: str) -> None:
        value = f"{tool_name}: {' '.join(summary.split())}".strip(": ").strip()
        if not value:
            return
        tool_results = list(self.retrieve("tool_results", []))
        if value not in tool_results:
            tool_results.append(value)
        self.update("tool_results", tool_results)

    def add_queries(self, queries: list[dict[str, str]]) -> list[dict[str, str]]:
        existing = list(self.retrieve("generated_queries", []))
        seen = {item.get("query", "").strip().lower() for item in existing}
        added: list[dict[str, str]] = []

        for item in queries:
            query = " ".join(str(item.get("query", "")).split())
            goal = " ".join(str(item.get("research_goal", "")).split())
            if not query:
                continue
            normalized = query.lower()
            if normalized in seen:
                continue
            record = {"query": query, "research_goal": goal}
            existing.append(record)
            added.append(record)
            seen.add(normalized)

        self.update("generated_queries", existing)
        return added

    def add_insights(self, insights: list[str], minimum_quality: float = 0.35) -> list[str]:
        existing = list(self.retrieve("insights", []))
        added: list[str] = []

        for insight in insights:
            cleaned = " ".join(str(insight).split())
            if not cleaned:
                continue
            if self._insight_quality(cleaned) < minimum_quality:
                continue

            duplicate_index = self._duplicate_index(existing, cleaned)
            if duplicate_index is None:
                existing.append(cleaned)
                added.append(cleaned)
                continue

            if len(cleaned) > len(existing[duplicate_index]):
                existing[duplicate_index] = cleaned

        self.update("insights", existing)
        return added

    def add_follow_up_questions(self, questions: list[str]) -> list[str]:
        existing = list(self.retrieve("follow_up_questions", []))
        seen = {item.lower() for item in existing}
        added: list[str] = []

        for question in questions:
            cleaned = " ".join(str(question).split())
            if not cleaned:
                continue
            normalized = cleaned.lower()
            if normalized in seen:
                continue
            existing.append(cleaned)
            added.append(cleaned)
            seen.add(normalized)

        self.update("follow_up_questions", existing)
        return added

    def add_sources(self, sources: list[dict[str, str]]) -> list[dict[str, str]]:
        existing = list(self.retrieve("visited_sources", []))
        seen = {item.get("url", "").strip() for item in existing}
        added: list[dict[str, str]] = []

        for item in sources:
            url = str(item.get("url", "")).strip()
            if not url or url in seen:
                continue
            record = {
                "title": str(item.get("title", "")).strip(),
                "url": url,
                "snippet": str(item.get("snippet", "")).strip(),
                "source": str(item.get("source", "")).strip(),
                "year": str(item.get("year", "")).strip(),
            }
            existing.append(record)
            added.append(record)
            seen.add(url)

        self.update("visited_sources", existing)
        return added

    def snapshot(self, max_chars: int = 4000) -> str:
        blocks: list[str] = []
        notes = list(self.retrieve("notes", []))
        insights = list(self.retrieve("insights", []))
        questions = list(self.retrieve("follow_up_questions", []))
        queries = list(self.retrieve("generated_queries", []))
        tool_results = list(self.retrieve("tool_results", []))

        if notes:
            blocks.append("Working notes:\n- " + "\n- ".join(notes[:8]))
        if insights:
            blocks.append("Research learnings:\n- " + "\n- ".join(insights[:12]))
        if questions:
            blocks.append("Follow-up directions:\n- " + "\n- ".join(questions[:8]))
        if queries:
            blocks.append("Generated queries:\n- " + "\n- ".join(item["query"] for item in queries[:8]))
        if tool_results:
            blocks.append("Tool observations:\n- " + "\n- ".join(tool_results[:8]))

        snapshot = "\n\n".join(blocks).strip()
        return snapshot[:max_chars]

    def export_deep_research(
        self,
        breadth_used: int,
        depth_requested: int,
        depth_completed: int,
    ) -> dict:
        return {
            "breadth_used": breadth_used,
            "depth_requested": depth_requested,
            "depth_completed": depth_completed,
            "follow_up_questions": list(self.retrieve("follow_up_questions", [])),
            "generated_queries": list(self.retrieve("generated_queries", [])),
            "learnings": list(self.retrieve("insights", [])),
            "visited_sources": list(self.retrieve("visited_sources", [])),
        }

    def _duplicate_index(self, existing: list[str], candidate: str) -> int | None:
        normalized_candidate = self._normalize(candidate)
        for index, current in enumerate(existing):
            normalized_current = self._normalize(current)
            if normalized_candidate == normalized_current:
                return index
            if normalized_candidate in normalized_current or normalized_current in normalized_candidate:
                return index
        return None

    def _insight_quality(self, text: str) -> float:
        words = text.split()
        if len(words) < 5:
            return 0.0

        length_score = min(len(words) / 18, 1.0)
        specificity_bonus = 0.15 if any(char.isdigit() for char in text) else 0.0
        structure_bonus = 0.1 if any(token in text.lower() for token in ["because", "compared", "benchmark", "dataset", "year", "method", "model"]) else 0.0
        return min(length_score * 0.6 + specificity_bonus + structure_bonus, 1.0)

    def _normalize(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
