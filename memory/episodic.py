from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class EpisodicMemory:
    """Placeholder for session/run history memory."""

    events: list[str] = field(default_factory=list)

    def record(self, event: str) -> None:
        if event.strip():
            self.events.append(event.strip())
