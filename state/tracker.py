from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class TrackingEvent:
    step: str
    detail: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(slots=True)
class ProgressTracker:
    events: list[TrackingEvent] = field(default_factory=list)
    total_depth: int = 0
    current_depth: int = 0
    total_breadth: int = 0
    current_breadth: int = 0
    total_queries: int = 0
    completed_queries: int = 0
    current_query: str = ""
    depths_completed: int = 0

    def mark(self, step: str, detail: str = "") -> None:
        self.events.append(TrackingEvent(step=step, detail=detail))

    def configure(self, depth: int, breadth: int) -> None:
        self.total_depth = depth
        self.current_depth = depth
        self.total_breadth = breadth
        self.current_breadth = breadth
        self.mark("configure", f"Configured deep research with depth={depth}, breadth={breadth}")

    def start_depth(self, remaining_depth: int, breadth: int, query_count: int) -> None:
        self.current_depth = remaining_depth
        self.current_breadth = breadth
        self.total_queries += query_count
        self.mark(
            "depth_start",
            f"Starting depth layer {self.total_depth - remaining_depth + 1} with {query_count} queries",
        )

    def start_query(self, query: str) -> None:
        self.current_query = query
        self.mark("query_start", query)

    def finish_query(self, query: str, result_count: int, learning_count: int) -> None:
        self.completed_queries += 1
        self.current_query = query
        self.mark(
            "query_complete",
            f"{query} | results={result_count} | learnings={learning_count}",
        )

    def complete_depth(self, remaining_depth: int) -> None:
        self.depths_completed = max(self.depths_completed, self.total_depth - remaining_depth + 1)
        self.mark(
            "depth_complete",
            f"Completed depth layer {self.total_depth - remaining_depth + 1}",
        )

    def latest(self) -> TrackingEvent | None:
        if not self.events:
            return None
        return self.events[-1]
