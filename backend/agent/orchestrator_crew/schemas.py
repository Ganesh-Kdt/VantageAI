"""
Pydantic schemas for the Orchestrator crew.

The OrchestratorCrew takes a raw user transcript and produces an
`OrchestratorResponse` containing a `DispatchPlan` — the structured input the
downstream EDGAR and web-search sub-agents consume. The orchestrator does not
execute the plan itself.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


Intent = Literal["first_look", "head_to_head", "digest", "clarify"]
FilingType = Literal["10-K", "10-Q", "8-K"]
WebCategory = Literal[
    "news",
    "pricing",
    "product",
    "hiring",
    "reviews",
    "funding",
    "exec_moves",
    "comparison",
    "general",
]


class CompanyRef(BaseModel):
    name: str = Field(..., description="Canonical company name, e.g. 'Salesforce'.")
    ticker: Optional[str] = Field(
        None,
        description="Uppercase ticker if the company is publicly listed in the US. Null for private companies or when unknown.",
    )
    is_public: bool = Field(
        False,
        description="True only if the company is a known US-listed public company with a ticker.",
    )


class EdgarQuery(BaseModel):
    company: str
    ticker: Optional[str] = None
    filing_types: List[FilingType] = Field(default_factory=lambda: ["10-K"])
    focus: str = Field(
        "",
        description="Free-text hint describing what to extract from the filing — e.g. 'revenue segments, pricing power'.",
    )


class WebQuery(BaseModel):
    query: str = Field(..., description="Concrete search query for You.com.")
    category: WebCategory = "general"


class DispatchPlan(BaseModel):
    intent: Intent
    companies: List[CompanyRef] = Field(default_factory=list)
    edgar_queries: List[EdgarQuery] = Field(default_factory=list)
    web_queries: List[WebQuery] = Field(default_factory=list)
    timeframe_days: int = Field(
        90,
        description="How far back sub-agents should scope their search. Default 90 days; use 7 for digest intent.",
    )
    priority_fields: List[str] = Field(
        default_factory=list,
        description="Report fields the user emphasized — e.g. ['pricing_signals'] if they asked about pricing.",
    )


class OrchestratorResponse(BaseModel):
    plan: DispatchPlan
    normalized_query: str = Field(
        "",
        description="One-sentence restatement of what the user asked for, in analyst-speak.",
    )
    needs_clarification: bool = False
    clarification_prompt: Optional[str] = None
