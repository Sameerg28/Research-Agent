from typing import Literal

from pydantic import BaseModel, Field


class Understanding(BaseModel):
    simple_explanation: str = ""
    one_line_core: str = ""
    mental_model: str = ""
    why_it_matters: str = ""


class TechnicalSummary(BaseModel):
    problem: str = ""
    method: str = ""
    result: str = ""


class Relevance(BaseModel):
    learning: bool = False
    memory: bool = False
    efficiency: bool = False
    autonomy: bool = False


class ImplementationIdea(BaseModel):
    idea: str = ""
    description: str = ""
    feasibility: Literal["HIGH", "MEDIUM", "LOW"] = "MEDIUM"


class ApplicationToErisia(BaseModel):
    relevance: Relevance = Field(default_factory=Relevance)
    key_takeaways: list[str] = Field(default_factory=list)
    implementation_ideas: list[ImplementationIdea] = Field(default_factory=list)
    experiment_suggestions: list[str] = Field(default_factory=list)


class CriticalAnalysis(BaseModel):
    limitations: str = ""
    overhyped_parts: str = ""
    real_value: str = ""


class ResearchQuery(BaseModel):
    query: str = ""
    research_goal: str = ""


class VisitedSource(BaseModel):
    title: str = ""
    url: str = ""
    snippet: str = ""
    source: str = ""
    year: str = ""


class DeepResearch(BaseModel):
    breadth_used: int = 0
    depth_requested: int = 0
    depth_completed: int = 0
    follow_up_questions: list[str] = Field(default_factory=list)
    generated_queries: list[ResearchQuery] = Field(default_factory=list)
    learnings: list[str] = Field(default_factory=list)
    visited_sources: list[VisitedSource] = Field(default_factory=list)


class PaperAnalysis(BaseModel):
    paper_title: str = "Untitled Paper"
    context_version: str = "Unknown"
    understanding: Understanding = Field(default_factory=Understanding)
    technical_summary: TechnicalSummary = Field(default_factory=TechnicalSummary)
    application_to_erisia: ApplicationToErisia = Field(default_factory=ApplicationToErisia)
    critical_analysis: CriticalAnalysis = Field(default_factory=CriticalAnalysis)
    final_verdict: str = ""
    deep_research: DeepResearch = Field(default_factory=DeepResearch)
    report_markdown: str = ""


def validate(data: dict) -> dict:
    parsed = PaperAnalysis(**data)
    return parsed.model_dump()
