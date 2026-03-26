import argparse
import json
import sys
from pathlib import Path

from rich.console import Console

from cognition.decision import DecisionEngine, resolve_input_path, resolve_mode
from cognition.modes import available_modes
from config import DEFAULT_RESEARCH_BREADTH, DEFAULT_RESEARCH_DEPTH, DEFAULT_SEARCH_LIMIT
from core.logger import setup_logging
from core.renderer import render
from implementations.tool.groq_voice_transcriber import GroqVoiceTranscriber
from implementations.llm.groq_llm import GroqLLM
from implementations.memory.simple_memory import SimpleMemory
from implementations.search.openalex_search import OpenAlexSearch
from intelligence.evaluator import ResearchEvaluator
from intelligence.researcher import Researcher, build_session
from memory.working import WorkingMemory
from state.state import ProjectPaths, ResearchRequest
from state.tracker import ProgressTracker
from tools.file_handler import save_markdown_report, save_report

setup_logging()
console = Console()
paths = ProjectPaths.from_root()
paths.ensure_runtime_dirs()


def _fail(message: str, label: str = "Error") -> None:
    console.print(f"[red]{label}:[/red] {message}")
    sys.exit(1)


def _display_path(path: str) -> str:
    candidate = Path(path)
    try:
        return str(candidate.relative_to(paths.root))
    except ValueError:
        return str(candidate)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Erisia Research System - iterative paper analysis and deep research"
    )
    parser.add_argument(
        "--input",
        "--paper",
        dest="input_path",
        required=False,
        help="Path to the input paper (.pdf or .txt). If omitted, the app will prompt interactively.",
    )
    parser.add_argument(
        "--mode",
        choices=list(available_modes()),
        default=None,
        help="Analysis mode: understand | apply | dual",
    )
    parser.add_argument(
        "--breadth",
        type=int,
        default=DEFAULT_RESEARCH_BREADTH,
        help="How many external research queries to generate per layer.",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=DEFAULT_RESEARCH_DEPTH,
        help="How many recursive deep-research layers to run.",
    )
    parser.add_argument(
        "--search-limit",
        type=int,
        default=DEFAULT_SEARCH_LIMIT,
        help="How many external scholarly results to pull per query.",
    )
    parser.add_argument(
        "--no-web",
        action="store_false",
        dest="include_web",
        help="Disable the external deep-research loop and only analyze the paper itself.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save output JSON and markdown report to outputs/reports/",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_only",
        help="Print raw JSON output only (no rich rendering)",
    )
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Enable voice input for interactive prompts",
    )
    return parser


def _print_run_header(session) -> None:
    console.print(
        f"[dim]Mode:[/dim] [bold]{session.request.mode}[/bold]  |  "
        f"[dim]Input:[/dim] {_display_path(session.request.input_path)}  |  "
        f"[dim]Words:[/dim] {session.word_count:,}  |  "
        f"[dim]Breadth:[/dim] {session.request.breadth}  |  "
        f"[dim]Depth:[/dim] {session.request.depth}  |  "
        f"[dim]Web:[/dim] {'on' if session.request.include_web else 'off'}"
    )
    console.print("[dim]Analyzing and researching...[/dim]\n")


def _build_researcher() -> Researcher:
    memory_backend = SimpleMemory()
    memory = WorkingMemory(memory_backend)
    llm = GroqLLM()
    search = OpenAlexSearch()
    evaluator = ResearchEvaluator()
    decision_engine = DecisionEngine(memory)
    researcher = Researcher(
        memory=memory,
        llm=llm,
        search=search,
        evaluator=evaluator,
        decision_engine=decision_engine,
    )
    return researcher


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    voice_input = None
    if args.voice:
        try:
            from core.voice import VoiceInput
        except Exception as exc:  # pragma: no cover - depends on optional audio stack
            _fail(f"Voice mode could not be initialized: {exc}")
        voice_input = VoiceInput(GroqVoiceTranscriber())

    try:
        input_path = resolve_input_path(
            explicit_path=args.input_path,
            paths=paths,
            console=console,
            use_voice=args.voice,
            voice_input=voice_input,
        )
        mode = resolve_mode(
            explicit_mode=args.mode,
            json_only=args.json_only,
            console=console,
            use_voice=args.voice,
            voice_input=voice_input,
        )
        request = ResearchRequest(
            input_path=input_path,
            mode=mode,
            breadth=max(0, args.breadth),
            depth=max(0, args.depth),
            search_limit=max(1, args.search_limit),
            include_web=bool(args.include_web),
            save_output=args.save,
            json_only=args.json_only,
            use_voice=args.voice,
        )
        session = build_session(request, paths)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        _fail(str(exc))

    _print_run_header(session)

    researcher = _build_researcher()
    tracker = ProgressTracker()

    try:
        result = researcher.run(session, tracker=tracker)
    except ValueError as exc:
        _fail(str(exc), label="Validation Error")
    except json.JSONDecodeError as exc:
        _fail(str(exc), label="JSON Parse Error")
    except Exception as exc:
        _fail(str(exc), label="API Error")

    if request.json_only:
        print(json.dumps(result, indent=2))
    else:
        render(result, request.mode)

    if request.save_output:
        json_path = save_report(result, request.input_path, request.mode, paths)
        markdown_path = save_markdown_report(
            result.get("report_markdown", ""),
            request.input_path,
            request.mode,
            paths,
        )
        console.print(f"[dim]JSON saved -> {_display_path(str(json_path))}[/dim]")
        if markdown_path is not None:
            console.print(f"[dim]Markdown saved -> {_display_path(str(markdown_path))}[/dim]")


if __name__ == "__main__":
    main()
