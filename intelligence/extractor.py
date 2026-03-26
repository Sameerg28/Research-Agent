from __future__ import annotations

from cognition.modes import build_system_prompt, build_user_prompt
from interfaces.llm import LLMInterface
from interfaces.memory import MemoryInterface
from state.state import ResearchSession
from state.tracker import ProgressTracker


def extract_knowledge(
    session: ResearchSession,
    llm: LLMInterface,
    memory: MemoryInterface,
    tracker: ProgressTracker | None = None,
) -> dict:
    system_prompt = build_system_prompt(
        mode=session.request.mode,
        erisia_context=session.context_text,
        working_memory=memory.snapshot(),
        word_count=session.word_count,
    )
    user_prompt = build_user_prompt(
        paper_text=session.paper_text,
        source_path=session.request.input_path,
    )

    if tracker is not None:
        tracker.mark("llm", "Prepared prompts for structured paper extraction")

    return llm.generate(system_prompt, user_prompt, allow_chunking=True)
