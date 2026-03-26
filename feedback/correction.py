from __future__ import annotations

from copy import deepcopy

DEFAULT_ANALYSIS = {
    "paper_title": "Untitled Paper",
    "context_version": "Unknown",
    "understanding": {
        "simple_explanation": "",
        "one_line_core": "",
        "mental_model": "",
        "why_it_matters": "",
    },
    "technical_summary": {
        "problem": "",
        "method": "",
        "result": "",
    },
    "application_to_erisia": {
        "relevance": {
            "learning": False,
            "memory": False,
            "efficiency": False,
            "autonomy": False,
        },
        "key_takeaways": [],
        "implementation_ideas": [],
        "experiment_suggestions": [],
    },
    "critical_analysis": {
        "limitations": "",
        "overhyped_parts": "",
        "real_value": "",
    },
    "final_verdict": "",
}


def correct_analysis(data: dict | None) -> dict:
    corrected = deepcopy(DEFAULT_ANALYSIS)
    if isinstance(data, dict):
        _merge_dicts(corrected, data)

    corrected["paper_title"] = _as_text(corrected.get("paper_title"), "Untitled Paper")
    corrected["context_version"] = _as_text(corrected.get("context_version"), "Unknown")
    corrected["final_verdict"] = _as_text(corrected.get("final_verdict"))

    for section in ("understanding", "technical_summary", "critical_analysis"):
        corrected[section] = _normalize_text_block(
            corrected.get(section),
            DEFAULT_ANALYSIS[section],
        )

    application = corrected.get("application_to_erisia", {})
    if not isinstance(application, dict):
        application = deepcopy(DEFAULT_ANALYSIS["application_to_erisia"])

    relevance = application.get("relevance", {})
    if not isinstance(relevance, dict):
        relevance = {}
    application["relevance"] = {
        "learning": bool(relevance.get("learning", False)),
        "memory": bool(relevance.get("memory", False)),
        "efficiency": bool(relevance.get("efficiency", False)),
        "autonomy": bool(relevance.get("autonomy", False)),
    }
    application["key_takeaways"] = _string_list(application.get("key_takeaways"), limit=6)
    application["experiment_suggestions"] = _string_list(
        application.get("experiment_suggestions"),
        limit=4,
    )
    application["implementation_ideas"] = _normalize_ideas(
        application.get("implementation_ideas"),
        limit=5,
    )
    corrected["application_to_erisia"] = application

    return corrected


def _merge_dicts(target: dict, source: dict) -> None:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge_dicts(target[key], value)
        else:
            target[key] = value


def _normalize_text_block(value: object, template: dict[str, str]) -> dict[str, str]:
    if not isinstance(value, dict):
        value = {}
    return {
        key: _as_text(value.get(key), default)
        for key, default in template.items()
    }


def _normalize_ideas(value: object, limit: int) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    ideas: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue

        feasibility = _as_text(item.get("feasibility"), "MEDIUM").upper()
        if feasibility not in {"HIGH", "MEDIUM", "LOW"}:
            feasibility = "MEDIUM"

        ideas.append(
            {
                "idea": _as_text(item.get("idea")),
                "description": _as_text(item.get("description")),
                "feasibility": feasibility,
            }
        )

    return ideas[:limit]


def _string_list(value: object, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_as_text(item) for item in value if _as_text(item)][:limit]


def _as_text(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default
