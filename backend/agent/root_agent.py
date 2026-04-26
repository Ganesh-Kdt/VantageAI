from crewai import Agent, Crew, Task, Process
from backend.agent.tools_registry import baseten_llm, edgar_search_tool
from backend.agent.web_search_agents import web_search_agent, build_web_search_tasks
from backend.agent.prompts import SYSTEM_PROMPT


# ── Edgar agent (teammate owns the implementation) ───────────────────────────

edgar_agent = Agent(
    role="SEC EDGAR Researcher",
    goal="Retrieve authoritative financial data from SEC EDGAR filings for a public company.",
    backstory=(
        "You are a financial filings specialist who extracts revenue, risk factors, "
        "and material events from SEC 10-K, 10-Q, and 8-K filings. "
        "You always cite the exact filing URL and date."
    ),
    tools=[edgar_search_tool],
    llm=baseten_llm,
    verbose=True,
)


# ── Summarize agent ───────────────────────────────────────────────────────────

summarize_agent = Agent(
    role="Competitive Intelligence Analyst",
    goal=(
        "Synthesise the web research and SEC EDGAR findings into a structured, "
        "risk-scored intelligence report in valid JSON. Score financial, legal, market, "
        "and management risk 1-10. Every claim must have a citation."
    ),
    backstory=(
        "You are a senior analyst at a top-tier strategy firm. You receive raw research "
        "from multiple parallel agents and produce clear, actionable JSON intelligence. "
        "You never fabricate data and always return valid JSON with no markdown fences."
    ),
    tools=[],
    llm=baseten_llm,
    verbose=True,
)


# ── Crew factory ──────────────────────────────────────────────────────────────

def build_first_look_crew(company: str, prompt: str = "") -> Crew:
    # 5 parallel web search tasks — one agent, five topics
    web_tasks = build_web_search_tasks(company, prompt)

    # 1 parallel edgar task
    edgar_task = Task(
        description=(
            f"Retrieve SEC EDGAR filing data for '{company}'. "
            f"Search for the most recent 10-K and any material 8-K filings. "
            f"If the company is private and has no filings, clearly note that."
        ),
        expected_output=(
            f"SEC filing citation for {company}: filing type, date, URL, and key financial figures. "
            f"Note 'private company — no SEC filings' if not found."
        ),
        agent=edgar_agent,
        async_execution=True,
    )

    # All 6 tasks (5 web + 1 edgar) run in parallel, then summarize
    all_research = web_tasks + [edgar_task]

    summarize_task = Task(
        description=(
            f"Using the web research and SEC EDGAR findings provided, produce a structured "
            f"intelligence report for '{company}'. "
            f"Follow this exact JSON structure:\n{SYSTEM_PROMPT}\n"
            f"Return ONLY the JSON object. No markdown fences. No preamble."
        ),
        expected_output="A valid JSON object matching the structure defined in the system prompt.",
        agent=summarize_agent,
        context=all_research,
    )

    return Crew(
        agents=[web_search_agent, edgar_agent, summarize_agent],
        tasks=[*all_research, summarize_task],
        process=Process.sequential,
        verbose=True,
    )
