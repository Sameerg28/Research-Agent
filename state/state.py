from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

AnalysisMode = Literal["understand", "apply", "dual"]


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    root: Path
    context_dir: Path
    context_file: Path
    input_root: Path
    pdf_inputs_dir: Path
    text_inputs_dir: Path
    outputs_dir: Path
    reports_dir: Path
    logs_dir: Path

    @classmethod
    def from_root(cls, root: Path | None = None) -> "ProjectPaths":
        base = Path(root) if root is not None else Path(__file__).resolve().parent.parent
        return cls(
            root=base,
            context_dir=base / "context",
            context_file=base / "context" / "erisia.txt",
            input_root=base / "inputs",
            pdf_inputs_dir=base / "inputs" / "pdfs",
            text_inputs_dir=base / "inputs" / "text",
            outputs_dir=base / "outputs",
            reports_dir=base / "outputs" / "reports",
            logs_dir=base / "logs",
        )

    def ensure_runtime_dirs(self) -> None:
        self.context_dir.mkdir(exist_ok=True)
        self.input_root.mkdir(exist_ok=True)
        self.pdf_inputs_dir.mkdir(exist_ok=True)
        self.text_inputs_dir.mkdir(exist_ok=True)
        self.outputs_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

    def report_path(
        self,
        input_path: str | Path,
        mode: AnalysisMode,
        timestamp: datetime | None = None,
    ) -> Path:
        stamp = timestamp or datetime.now()
        stem = Path(input_path).stem
        return self.reports_dir / f"{stem}_{mode}_{stamp:%Y%m%d_%H%M%S}.json"

    def markdown_report_path(
        self,
        input_path: str | Path,
        mode: AnalysisMode,
        timestamp: datetime | None = None,
    ) -> Path:
        stamp = timestamp or datetime.now()
        stem = Path(input_path).stem
        return self.reports_dir / f"{stem}_{mode}_{stamp:%Y%m%d_%H%M%S}.md"


@dataclass(frozen=True, slots=True)
class ResearchRequest:
    input_path: str
    mode: AnalysisMode
    breadth: int = 3
    depth: int = 2
    search_limit: int = 4
    include_web: bool = True
    save_output: bool = False
    json_only: bool = False
    use_voice: bool = False


@dataclass(slots=True)
class ResearchSession:
    request: ResearchRequest
    paper_text: str
    context_text: str

    @property
    def word_count(self) -> int:
        return len(self.paper_text.split())

    @property
    def source_name(self) -> str:
        return Path(self.request.input_path).name
