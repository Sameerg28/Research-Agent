from __future__ import annotations

import json
from pathlib import Path

from state.state import AnalysisMode, ProjectPaths


def list_inputs(paths: ProjectPaths) -> list[Path]:
    paths.ensure_runtime_dirs()
    inputs = [
        *paths.pdf_inputs_dir.glob("*.pdf"),
        *paths.text_inputs_dir.glob("*.txt"),
    ]
    return sorted(inputs, key=lambda path: (path.suffix.lower(), path.name.lower()))


def load_document(path: str | Path) -> str:
    document_path = Path(path)
    if not document_path.exists():
        raise FileNotFoundError(f"File not found: {document_path}")

    if document_path.suffix.lower() == ".pdf":
        return _load_pdf_text(document_path)

    text = document_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Input file is empty: {document_path}")
    return text


def _load_pdf_text(document_path: Path) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("pymupdf is not installed. Run: pip install pymupdf") from exc

    document = fitz.open(str(document_path))
    try:
        text = "\n".join(page.get_text() for page in document).strip()
    finally:
        document.close()

    if not text:
        raise ValueError("PDF appears to be empty or scanned with no extractable text.")
    return text


def load_context(paths: ProjectPaths) -> str:
    if paths.context_file.exists():
        return paths.context_file.read_text(encoding="utf-8").strip()
    return ""


def save_report(
    data: dict,
    input_path: str | Path,
    mode: AnalysisMode,
    paths: ProjectPaths,
) -> Path:
    paths.ensure_runtime_dirs()
    report_path = paths.report_path(input_path, mode)
    report_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return report_path


def save_markdown_report(
    report_markdown: str,
    input_path: str | Path,
    mode: AnalysisMode,
    paths: ProjectPaths,
) -> Path | None:
    report_markdown = report_markdown.strip()
    if not report_markdown:
        return None
    paths.ensure_runtime_dirs()
    report_path = paths.markdown_report_path(input_path, mode)
    report_path.write_text(report_markdown, encoding="utf-8")
    return report_path
