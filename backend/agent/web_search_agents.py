from crewai import Agent, Task
from backend.agent.tools_registry import baseten_llm, web_search_tool

web_search_agent = Agent(
    role="Web Search Researcher",
    goal="Research a company using live web search. Cover one specific topic per task.",
    backstory=(
        "You are a web researcher who uses deep search to find cited intelligence "
        "about companies. You never fabricate data and always include source URLs."
    ),
    tools=[web_search_tool],
    llm=baseten_llm,
    verbose=True,
)


def build_web_search_tasks(company: str, prompt: str = "") -> list[Task]:
    """
    Returns 5 parallel web search tasks for `company`, each covering a different topic.
    All tasks are assigned to the same web_search_agent and run with async_execution=True.
    Pass the returned list as context to the summarize agent's task.
    """
    focus = f" Orchestrator focus: {prompt}" if prompt else ""

    return [
        Task(
            description=(
                f"Research the financial health of '{company}'.{focus} "
                f"Search for '{company} revenue funding valuation 2024', "
                f"'{company} profitability burn rate', '{company} earnings'."
            ),
            expected_output=f"Cited financial facts about {company} with source URLs.",
            agent=web_search_agent,
            async_execution=True,
        ),
        Task(
            description=(
                f"Research the hiring trends and future headcount of '{company}'.{focus} "
                f"Search for '{company} hiring headcount 2024', '{company} job openings layoffs', "
                f"'{company} workforce expansion'."
            ),
            expected_output=f"Cited hiring signals for {company} with source URLs.",
            agent=web_search_agent,
            async_execution=True,
        ),
        Task(
            description=(
                f"Research the product and technology moves of '{company}'.{focus} "
                f"Search for '{company} product launch 2024', '{company} new features roadmap', "
                f"'{company} technology stack R&D'."
            ),
            expected_output=f"Cited product intelligence for {company} with source URLs.",
            agent=web_search_agent,
            async_execution=True,
        ),
        Task(
            description=(
                f"Research recent news and leadership changes at '{company}'.{focus} "
                f"Search for '{company} news last 90 days', '{company} CEO executive change', "
                f"'{company} acquisition partnership lawsuit'."
            ),
            expected_output=f"Cited recent news and leadership events for {company} with source URLs.",
            agent=web_search_agent,
            async_execution=True,
        ),
        Task(
            description=(
                f"Research the competitive positioning of '{company}'.{focus} "
                f"Search for '{company} vs competitors market share', "
                f"'{company} G2 Capterra reviews', '{company} pricing strategy'."
            ),
            expected_output=f"Cited competitive signals for {company} with source URLs.",
            agent=web_search_agent,
            async_execution=True,
        ),
    ]
