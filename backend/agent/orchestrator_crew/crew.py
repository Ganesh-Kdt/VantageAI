"""
OrchestratorCrew — CrewAI @CrewBase assembly for the orchestrator agent.

Takes a raw user transcript and returns an OrchestratorResponse containing a
structured DispatchPlan for the downstream EDGAR and web-search sub-agents.
"""
from __future__ import annotations

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from backend.agent.orchestrator_crew.schemas import OrchestratorResponse
from backend.agent.root_agent import baseten_llm
from backend.agent.tools.edgar_tool import TICKER_TO_CIK


KNOWN_TICKERS = ", ".join(sorted(TICKER_TO_CIK.keys()))


@CrewBase
class OrchestratorCrew:
    """Single-agent crew that plans sub-agent dispatch from a user transcript."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def planner(self) -> Agent:
        return Agent(
            config=self.agents_config["planner"],
            llm=baseten_llm,
            allow_delegation=False,
            verbose=False,
        )

    @task
    def plan_dispatch(self) -> Task:
        return Task(
            config=self.tasks_config["plan_dispatch"],
            output_pydantic=OrchestratorResponse,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )


def run_orchestrator(transcript: str) -> OrchestratorResponse:
    """Convenience wrapper — kickoff the crew with a transcript and return the typed response."""
    result = OrchestratorCrew().crew().kickoff(
        inputs={"transcript": transcript, "known_tickers": KNOWN_TICKERS}
    )
    if hasattr(result, "pydantic") and result.pydantic is not None:
        return result.pydantic
    # Fallback: parse from raw text if CrewAI couldn't coerce into pydantic
    import json
    raw = str(result).strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])
    return OrchestratorResponse(**json.loads(raw))
