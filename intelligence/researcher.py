from __future__ import annotations

from pathlib import Path

from config import (
    DEFAULT_FOLLOW_UP_QUESTIONS,
    DEFAULT_LEARNINGS_PER_QUERY,
    REPORT_MAX_LEARNINGS,
)
from cognition.decision import DecisionEngine
from cognition.modes import (
    build_report_prompts,
    build_research_plan_prompts,
    build_research_synthesis_prompts,
)
from core.logger import log_error, log_result
from feedback.correction import correct_analysis
from feedback.validator import validate
from intelligence.evaluator import ResearchEvaluator
from intelligence.expander import expand_context
from intelligence.extractor import extract_knowledge
from interfaces.llm import LLMInterface
from interfaces.memory import MemoryInterface
from interfaces.search import SearchInterface
from interfaces.tool import ToolInterface
from state.state import ProjectPaths, ResearchRequest, ResearchSession
from state.tracker import ProgressTracker
from tools.file_handler import load_context, load_document
from tools.web import WebSearchTool


class Researcher:
    def __init__(
        self,
        memory: MemoryInterface,
        llm: LLMInterface,
        search: SearchInterface,
        *,
        evaluator: ResearchEvaluator | None = None,
        decision_engine: DecisionEngine | None = None,
        web_tool: ToolInterface | None = None,
        minimum_path_score: float = 0.35,
    ) -> None:
        self._memory = memory
        self._llm = llm
        self._search = search
        self._evaluator = evaluator or ResearchEvaluator()
        self._decision_engine = decision_engine or DecisionEngine(memory)
        self._web_tool = web_tool or WebSearchTool(search)
        self._minimum_path_score = minimum_path_score

    def run(self, session: ResearchSession, tracker: ProgressTracker | None = None) -> dict:
        progress = tracker or ProgressTracker()
        progress.configure(session.request.depth, session.request.breadth)
        progress.mark("load", "Prepared session data")
        self._memory.update("best_score", 0.0)

        try:
            expand_context(session, self._memory, web_tool=self._web_tool, tracker=progress)
            raw_analysis = extract_knowledge(session, self._llm, self._memory, progress)
            corrected = correct_analysis(raw_analysis)
            analysis = validate(corrected)

            if session.request.include_web and session.request.depth > 0 and session.request.breadth > 0:
                seed_focus = self._build_seed_focus(session, analysis)
                self._deep_research(
                    session=session,
                    analysis=analysis,
                    seed_focus=seed_focus,
                    remaining_depth=session.request.depth,
                    breadth=session.request.breadth,
                    tracker=progress,
                )

            deep_research_bundle = self._memory.export_deep_research(
                breadth_used=session.request.breadth,
                depth_requested=session.request.depth,
                depth_completed=progress.depths_completed,
            )
            report_markdown = self._write_markdown_report(session, analysis, deep_research_bundle)

            final_result = validate(
                {
                    **analysis,
                    "deep_research": deep_research_bundle,
                    "report_markdown": report_markdown,
                }
            )
        except Exception as exc:
            log_error(exc, session.request.input_path, 0)
            progress.mark("error", str(exc))
            raise

        log_result(final_result, session.request.input_path, session.request.mode)
        progress.mark("complete", "Structured analysis and deep research ready")
        return final_result

    def _deep_research(
        self,
        session: ResearchSession,
        analysis: dict,
        seed_focus: str,
        remaining_depth: int,
        breadth: int,
        tracker: ProgressTracker,
    ) -> None:
        if remaining_depth <= 0 or breadth <= 0:
            return

        plan = self._generate_research_plan(
            session=session,
            analysis=analysis,
            seed_focus=seed_focus,
            breadth=breadth,
        )
        queries = self._memory.add_queries(
            self._normalize_queries(plan.get("queries", []), limit=breadth)
        )
        self._memory.add_follow_up_questions(
            self._clean_string_list(plan.get("follow_up_questions", []), DEFAULT_FOLLOW_UP_QUESTIONS)
        )

        if not queries:
            tracker.complete_depth(remaining_depth)
            return

        tracker.start_depth(remaining_depth, breadth, len(queries))

        previous_best_score = float(self._memory.retrieve("best_score", 0.0) or 0.0)
        layer_best_score = previous_best_score
        layer_new_insights = 0
        next_directions: list[str] = []

        for item in queries:
            query = item["query"]
            research_goal = item["research_goal"]
            tracker.start_query(query)

            previous_insights = list(self._memory.retrieve("insights", []) or [])
            results = self._search.search(query, limit=session.request.search_limit)
            added_sources = self._memory.add_sources(results)

            if not results:
                tracker.finish_query(query, 0, 0)
                continue

            synthesis = self._synthesize_search_results(
                query=query,
                research_goal=research_goal,
                search_results=results[: session.request.search_limit],
                analysis=analysis,
                prior_learnings=previous_insights,
            )

            candidate_insights = self._clean_string_list(
                synthesis.get("learnings", []),
                DEFAULT_LEARNINGS_PER_QUERY,
            )
            candidate_follow_ups = self._clean_string_list(
                synthesis.get("follow_up_questions", []),
                DEFAULT_FOLLOW_UP_QUESTIONS,
            )

            new_insights = self._memory.add_insights(candidate_insights)
            evaluation = self._evaluator.evaluate(
                query=query,
                insights=new_insights or candidate_insights,
                sources=added_sources or results,
                previous_insights=previous_insights,
            )
            self._memory.record_tool_result(
                "evaluation",
                f"{query} -> score={evaluation['score']:.2f} ({evaluation['reason']})",
            )

            if evaluation["score"] < self._minimum_path_score:
                self._memory.record_tool_result("decision", f"Discarded low-quality path: {query}")
                tracker.finish_query(query, len(results), len(new_insights))
                continue

            self._memory.add_follow_up_questions(candidate_follow_ups)
            next_directions.extend(candidate_follow_ups)
            layer_new_insights += len(new_insights)
            layer_best_score = max(layer_best_score, float(evaluation["score"]))
            tracker.finish_query(query, len(results), len(new_insights))

        tracker.complete_depth(remaining_depth)
        improvement = max(layer_best_score - previous_best_score, 0.0)
        self._memory.update("best_score", layer_best_score)

        decision = self._decision_engine.decide(
            score=layer_best_score,
            improvement=improvement,
            new_insight_count=layer_new_insights,
            remaining_depth=remaining_depth,
            current_breadth=breadth,
        )
        self._memory.record_tool_result("decision", decision["reason"])

        if decision["action"] in {"stop_and_synthesize", "discard_low_quality_path"}:
            return

        next_focus = self._build_next_focus(session, analysis, next_directions)
        self._deep_research(
            session=session,
            analysis=analysis,
            seed_focus=next_focus,
            remaining_depth=remaining_depth - 1,
            breadth=int(decision.get("breadth", max(1, breadth // 2))),
            tracker=tracker,
        )

    def _generate_research_plan(
        self,
        session: ResearchSession,
        analysis: dict,
        seed_focus: str,
        breadth: int,
    ) -> dict:
        system_prompt, user_prompt = build_research_plan_prompts(
            analysis=analysis,
            erisia_context=session.context_text,
            working_memory=self._memory.snapshot(),
            breadth=breadth,
            question_limit=DEFAULT_FOLLOW_UP_QUESTIONS,
            seed_focus=seed_focus,
        )
        return self._llm.generate(system_prompt, user_prompt, allow_chunking=False)

    def _synthesize_search_results(
        self,
        query: str,
        research_goal: str,
        search_results: list[dict[str, str]],
        analysis: dict,
        prior_learnings: list[str],
    ) -> dict:
        system_prompt, user_prompt = build_research_synthesis_prompts(
            query=query,
            research_goal=research_goal,
            search_results=search_results,
            analysis=analysis,
            prior_learnings=prior_learnings,
            learning_limit=DEFAULT_LEARNINGS_PER_QUERY,
            question_limit=DEFAULT_FOLLOW_UP_QUESTIONS,
        )
        return self._llm.generate(system_prompt, user_prompt, allow_chunking=False)

    def _write_markdown_report(self, session: ResearchSession, analysis: dict, deep_research: dict) -> str:
        compact_bundle = {
            **deep_research,
            "learnings": deep_research.get("learnings", [])[:REPORT_MAX_LEARNINGS],
            "visited_sources": deep_research.get("visited_sources", [])[:12],
            "follow_up_questions": deep_research.get("follow_up_questions", [])[:8],
        }
        system_prompt, user_prompt = build_report_prompts(
            analysis=analysis,
            deep_research=compact_bundle,
            erisia_context=session.context_text,
        )
        response = self._llm.generate(system_prompt, user_prompt, allow_chunking=False)
        return str(response.get("report_markdown", "")).strip()

    def _build_seed_focus(self, session: ResearchSession, analysis: dict) -> str:
        implementation_ideas = analysis.get("application_to_erisia", {}).get("implementation_ideas", [])
        idea_titles = ", ".join(item.get("idea", "") for item in implementation_ideas if item.get("idea"))
        takeaways = ", ".join(analysis.get("application_to_erisia", {}).get("key_takeaways", [])[:3])
        return (
            f"Paper: {analysis.get('paper_title') or Path(session.request.input_path).stem}. "
            f"Investigate validation, criticism, related work, and practical implementation details. "
            f"Key takeaways: {takeaways or 'None yet'}. "
            f"Implementation ideas already surfaced: {idea_titles or 'None yet'}."
        )

    def _build_next_focus(
        self,
        session: ResearchSession,
        analysis: dict,
        next_directions: list[str],
    ) -> str:
        follow_up_pool = next_directions[:4] or list(self._memory.retrieve("follow_up_questions", []) or [])[-4:]
        learnings = list(self._memory.retrieve("insights", []) or [])[-6:]
        follow_up_block = "\n".join(f"- {item}" for item in follow_up_pool) or "- No explicit follow-up questions generated."
        learning_block = "\n".join(f"- {item}" for item in learnings) or "- No external learnings gathered yet."
        return (
            f"Continue researching {analysis.get('paper_title') or session.source_name}.\n"
            f"Latest learnings:\n{learning_block}\n"
            f"Next directions:\n{follow_up_block}"
        )

    def _normalize_queries(self, raw_queries: object, limit: int) -> list[dict[str, str]]:
        if not isinstance(raw_queries, list):
            return []

        normalized_queries: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in raw_queries:
            if not isinstance(item, dict):
                continue
            query = " ".join(str(item.get("query", "")).split())
            research_goal = " ".join(str(item.get("research_goal", "")).split())
            if not query:
                continue
            key = query.lower()
            if key in seen:
                continue
            normalized_queries.append({"query": query, "research_goal": research_goal})
            seen.add(key)
            if len(normalized_queries) >= limit:
                break
        return normalized_queries

    def _clean_string_list(self, value: object, limit: int) -> list[str]:
        if not isinstance(value, list):
            return []
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            text = " ".join(str(item).split())
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            cleaned.append(text)
            seen.add(key)
            if len(cleaned) >= limit:
                break
        return cleaned


def build_session(request: ResearchRequest, paths: ProjectPaths) -> ResearchSession:
    paper_text = load_document(request.input_path)
    context_text = load_context(paths)
    return ResearchSession(
        request=request,
        paper_text=paper_text,
        context_text=context_text,
    )
