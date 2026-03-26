from __future__ import annotations

import json
from datetime import datetime

from state.state import AnalysisMode

JSON_SCHEMA = """{
  "paper_title": "infer from content or write Untitled Paper",
  "context_version": "Erisia Context v1 or No context provided",
  "understanding": {
    "simple_explanation": "explain like teaching a sharp 15-year-old. Max 4 sentences.",
    "one_line_core": "compress the entire paper into one powerful sentence",
    "mental_model": "an analogy or intuitive frame to understand the idea",
    "why_it_matters": "why does this matter beyond any specific project? 2-3 sentences."
  },
  "technical_summary": {
    "problem": "",
    "method": "",
    "result": ""
  },
  "application_to_erisia": {
    "relevance": {
      "learning": true or false,
      "memory": true or false,
      "efficiency": true or false,
      "autonomy": true or false
    },
    "key_takeaways": ["", ""],
    "implementation_ideas": [
      {
        "idea": "short title",
        "description": "1-2 sentence explanation",
        "feasibility": "HIGH or MEDIUM or LOW"
      }
    ],
    "experiment_suggestions": ["", ""]
  },
  "critical_analysis": {
    "limitations": "",
    "overhyped_parts": "be honest and specific",
    "real_value": "what is genuinely useful"
  },
  "final_verdict": "1-2 sentence honest verdict on the paper's value"
}"""

PLAN_SCHEMA = """{
  "follow_up_questions": ["", ""],
  "queries": [
    {
      "query": "",
      "research_goal": ""
    }
  ]
}"""

SYNTHESIS_SCHEMA = """{
  "learnings": ["", ""],
  "follow_up_questions": ["", ""]
}"""

REPORT_SCHEMA = """{
  "report_markdown": "# ..."
}"""

MODE_BRIEFS: dict[AnalysisMode, str] = {
    "understand": "Prioritize the understanding layer. Keep application_to_erisia compact but still useful.",
    "apply": "Prioritize application_to_erisia. Keep the understanding layer concise and direct.",
    "dual": "Balance understanding and application with full depth across both layers.",
}


def available_modes() -> tuple[AnalysisMode, AnalysisMode, AnalysisMode]:
    return ("understand", "apply", "dual")


def _base_system(schema: str, extra_rules: list[str] | None = None) -> str:
    today = datetime.now().date().isoformat()
    rules = [
        f"You are Erisia's deep research strategist. Today is {today}.",
        "You explain hard ideas clearly, challenge hype, and connect theory to practical system design.",
        "You are not a generic summarizer.",
        "Return ONLY a valid JSON object.",
        "Match the requested schema exactly.",
        "Prefer precise, information-dense outputs over vague commentary.",
        "If the source material is uncertain or incomplete, say so plainly instead of inventing details.",
        "Schema:",
        schema,
    ]
    if extra_rules:
        rules.extend(extra_rules)
    return "\n".join(rules)


def _paper_scale_guidance(word_count: int | None) -> str:
    if word_count is None:
        return ""
    if word_count < 1500:
        return "Paper length signal: short input or abstract. Infer structure carefully and avoid over-claiming."
    if word_count < 6000:
        return "Paper length signal: standard paper. Balance explanation, critique, and application."
    return "Paper length signal: long paper. Synthesize recurring mechanisms and only keep the highest-value implementation ideas."


def _context_block(erisia_context: str) -> str:
    if erisia_context:
        return f"Erisia Context:\n{erisia_context}"
    return "No Erisia context provided. Fill application_to_erisia with generic research-agent and AI-system applications."


def _memory_block(working_memory: str) -> str:
    if not working_memory.strip():
        return ""
    return f"Working Memory Snapshot:\n{working_memory}"


def build_system_prompt(
    mode: AnalysisMode,
    erisia_context: str,
    working_memory: str = "",
    word_count: int | None = None,
) -> str:
    return "\n\n".join(
        section
        for section in [
            _base_system(
                JSON_SCHEMA,
                extra_rules=[
                    "Output rules:",
                    MODE_BRIEFS.get(mode, MODE_BRIEFS["dual"]),
                    '- Set context_version to "Erisia Context v1" when context text is present, otherwise "No context provided".',
                    "- Only mark relevance flags true when the paper genuinely supports that capability.",
                    "- Feasibility must be exactly HIGH, MEDIUM, or LOW.",
                    "- Be direct in critical_analysis and final_verdict.",
                ],
            ),
            _paper_scale_guidance(word_count),
            _context_block(erisia_context),
            _memory_block(working_memory),
        ]
        if section
    )


def build_user_prompt(paper_text: str, source_path: str | None = None) -> str:
    source_line = f"Source file: {source_path}\n\n" if source_path else ""
    return f"{source_line}Analyze this research paper:\n\n{paper_text}"


def build_research_plan_prompts(
    analysis: dict,
    erisia_context: str,
    working_memory: str,
    breadth: int,
    question_limit: int,
    seed_focus: str = "",
) -> tuple[str, str]:
    system_prompt = _base_system(
        PLAN_SCHEMA,
        extra_rules=[
            f"Return at most {breadth} queries.",
            f"Return at most {question_limit} follow-up questions.",
            "Queries should validate claims, surface adjacent work, find critiques, or uncover implementation details.",
            "Make every query materially different from the others.",
        ],
    )
    focus_block = f"Current research focus:\n{seed_focus}\n\n" if seed_focus else ""
    memory_snapshot = _memory_block(working_memory) or "Working Memory Snapshot:\nNone yet."
    user_prompt = (
        f"{focus_block}"
        "Generate the next external research plan for this paper analysis.\n\n"
        f"Paper analysis:\n{json.dumps(analysis, indent=2)}\n\n"
        f"{_context_block(erisia_context)}\n\n"
        f"{memory_snapshot}\n\n"
        "Return targeted scholarly research queries plus follow-up questions that would deepen understanding of the paper and its implications."
    )
    return system_prompt, user_prompt


def build_research_synthesis_prompts(
    query: str,
    research_goal: str,
    search_results: list[dict[str, str]],
    analysis: dict,
    prior_learnings: list[str],
    learning_limit: int,
    question_limit: int,
) -> tuple[str, str]:
    system_prompt = _base_system(
        SYNTHESIS_SCHEMA,
        extra_rules=[
            f"Return at most {learning_limit} learnings.",
            f"Return at most {question_limit} follow-up questions.",
            "Leverage exact names, years, methods, and contrasts when present.",
            "Keep learnings concise but information-dense.",
        ],
    )
    serialized_results = "\n\n".join(
        "\n".join(
            [
                f"Title: {item.get('title', '')}",
                f"URL: {item.get('url', '')}",
                f"Source: {item.get('source', '')}",
                f"Snippet: {item.get('snippet', '')}",
            ]
        )
        for item in search_results
    )
    learnings_block = "\n".join(f"- {item}" for item in prior_learnings[:12]) or "None yet."
    user_prompt = (
        "Synthesize external research findings for this paper.\n\n"
        f"Search query: {query}\n"
        f"Research goal: {research_goal or 'General validation and expansion'}\n\n"
        f"Paper analysis:\n{json.dumps(analysis, indent=2)}\n\n"
        f"Prior learnings:\n{learnings_block}\n\n"
        f"Search results:\n{serialized_results}"
    )
    return system_prompt, user_prompt


def build_report_prompts(
    analysis: dict,
    deep_research: dict,
    erisia_context: str,
) -> tuple[str, str]:
    system_prompt = _base_system(
        REPORT_SCHEMA,
        extra_rules=[
            "Write a polished markdown report.",
            "Use headings and compact bullet lists where useful.",
            "Include a Sources section that only lists sources provided in the input.",
        ],
    )
    user_prompt = (
        "Write a markdown report that combines the original paper analysis with the iterative deep research findings.\n\n"
        "Use these sections:\n"
        "# Title\n"
        "## Executive Summary\n"
        "## Paper Breakdown\n"
        "## Deep Research Learnings\n"
        "## Implications for Erisia\n"
        "## Open Questions\n"
        "## Sources\n\n"
        f"Paper analysis:\n{json.dumps(analysis, indent=2)}\n\n"
        f"Deep research bundle:\n{json.dumps(deep_research, indent=2)}\n\n"
        f"{_context_block(erisia_context)}"
    )
    return system_prompt, user_prompt
