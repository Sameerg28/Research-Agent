from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.prompt import IntPrompt, Prompt

from cognition.modes import available_modes
from interfaces.memory import MemoryInterface
from state.state import AnalysisMode, ProjectPaths
from tools.file_handler import list_inputs

if TYPE_CHECKING:
    from core.voice import VoiceInput

WORD_TO_NUMBER = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


class DecisionEngine:
    def __init__(
        self,
        memory: MemoryInterface,
        improvement_threshold: float = 0.05,
        low_quality_threshold: float = 0.35,
    ) -> None:
        self._memory = memory
        self._improvement_threshold = improvement_threshold
        self._low_quality_threshold = low_quality_threshold

    def decide(
        self,
        *,
        score: float,
        improvement: float,
        new_insight_count: int,
        remaining_depth: int,
        current_breadth: int,
    ) -> dict:
        follow_up_backlog = len(self._memory.retrieve("follow_up_questions", []) or [])

        if new_insight_count <= 0:
            return {
                "action": "stop_and_synthesize",
                "breadth": current_breadth,
                "reason": "No new insights were found.",
            }

        if score < self._low_quality_threshold:
            return {
                "action": "discard_low_quality_path",
                "breadth": current_breadth,
                "reason": f"Evaluation score {score:.2f} is below the quality threshold.",
            }

        if remaining_depth <= 1:
            return {
                "action": "stop_and_synthesize",
                "breadth": current_breadth,
                "reason": "Maximum depth has been reached.",
            }

        if improvement < self._improvement_threshold:
            return {
                "action": "stop_and_synthesize",
                "breadth": current_breadth,
                "reason": f"Score improvement {improvement:.2f} is below threshold.",
            }

        if follow_up_backlog > current_breadth and score >= 0.55:
            return {
                "action": "explore_more",
                "breadth": current_breadth + 1,
                "reason": "There are enough promising follow-up directions to widen the search.",
            }

        return {
            "action": "go_deeper",
            "breadth": max(1, current_breadth // 2),
            "reason": "The current path looks strong enough to continue deeper with tighter focus.",
        }


def resolve_input_path(
    explicit_path: str | None,
    paths: ProjectPaths,
    console: Console,
    use_voice: bool = False,
    voice_input: "VoiceInput | None" = None,
) -> str:
    if explicit_path:
        return explicit_path
    return select_input_interactively(
        paths=paths,
        console=console,
        use_voice=use_voice,
        voice_input=voice_input,
    )


def select_input_interactively(
    paths: ProjectPaths,
    console: Console,
    use_voice: bool = False,
    voice_input: "VoiceInput | None" = None,
) -> str:
    inputs = list_inputs(paths)
    if not inputs:
        raise FileNotFoundError(
            "No inputs found. Add a .pdf file to inputs/pdfs/ or a .txt file to inputs/text/."
        )

    console.print("\n[bold cyan]Available Inputs:[/bold cyan]")
    for index, input_path in enumerate(inputs, start=1):
        console.print(f"  [{index}] {_display_name(input_path, paths)}")

    if use_voice and voice_input is not None:
        console.print("\n[bold magenta]Voice Input Active[/bold magenta]")
        raw_voice = voice_input.get_input("Say the input number...")
        console.print(f"[dim]You said: {raw_voice}[/dim]")

        selection = _parse_voice_index(raw_voice)
        if selection is not None and 1 <= selection <= len(inputs):
            return str(inputs[selection - 1])

        console.print(
            "[yellow]Could not detect a valid input number from voice. Falling back to typing.[/yellow]"
        )

    selection = IntPrompt.ask(
        "\nSelect input number",
        choices=[str(index) for index in range(1, len(inputs) + 1)],
    )
    return str(inputs[selection - 1])


def resolve_mode(
    explicit_mode: AnalysisMode | None,
    json_only: bool,
    console: Console,
    use_voice: bool = False,
    voice_input: "VoiceInput | None" = None,
) -> AnalysisMode:
    if explicit_mode:
        return explicit_mode
    if json_only:
        return "dual"

    if use_voice and voice_input is not None:
        console.print("\n[bold magenta]Voice Input Active[/bold magenta]")
        raw_voice = voice_input.get_input("Say the mode: understand, apply, or dual...")
        console.print(f"[dim]You said: {raw_voice}[/dim]")
        parsed_mode = _parse_mode(raw_voice)
        if parsed_mode is not None:
            return parsed_mode
        console.print(
            "[yellow]Could not detect a valid mode from voice. Falling back to typing.[/yellow]"
        )

    selected = Prompt.ask(
        "Select mode",
        choices=list(available_modes()),
        default="dual",
    )
    return _parse_mode(selected) or "dual"


def _display_name(path: Path, paths: ProjectPaths) -> str:
    try:
        return str(path.relative_to(paths.input_root))
    except ValueError:
        return path.name


def _parse_voice_index(raw_voice: str) -> int | None:
    match = re.search(r"\d+", raw_voice)
    if match:
        return int(match.group())

    cleaned = raw_voice.lower().strip().strip(".")
    return WORD_TO_NUMBER.get(cleaned)


def _parse_mode(raw_text: str) -> AnalysisMode | None:
    cleaned = raw_text.lower().strip().strip(".")
    if cleaned in available_modes():
        return cleaned
    return None
