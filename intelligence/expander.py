from __future__ import annotations

from pathlib import Path

from interfaces.memory import MemoryInterface
from interfaces.tool import ToolInterface
from state.state import ResearchSession
from state.tracker import ProgressTracker


def expand_context(
    session: ResearchSession,
    memory: MemoryInterface,
    web_tool: ToolInterface | None = None,
    tracker: ProgressTracker | None = None,
) -> None:
    memory.remember(f"Mode selected: {session.request.mode}")
    memory.remember(f"Input file: {Path(session.request.input_path).name}")
    memory.remember(f"Document length: {session.word_count} words")

    if session.context_text:
        memory.remember("Erisia context is available for application mapping.")
    else:
        memory.remember(
            "No Erisia context file was loaded; application ideas should stay generic."
        )

    if web_tool is None:
        memory.record_tool_result("web", "No web-search tool is attached.")
        return

    query = Path(session.request.input_path).stem.replace("_", " ").strip()
    results = web_tool.execute({"query": query, "limit": 3})

    if isinstance(results, list) and results:
        titles = ", ".join(result.get("title", "") for result in results if result.get("title"))
        if titles:
            memory.record_tool_result("web", f"Supplemental titles: {titles}")
            if tracker is not None:
                tracker.mark("tools", "Collected supplemental web context")
            return

    memory.record_tool_result("web", "No live web results were available.")
    if tracker is not None:
        tracker.mark("tools", "No live web provider configured")
