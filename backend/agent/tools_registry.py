import os
from dotenv import load_dotenv
from crewai import LLM
from crewai.tools import tool
from backend.agent.tools.you_com_tool import search_web
from backend.agent.tools.edgar_tool import search_filings

load_dotenv()

BASETEN_API_KEY = os.getenv("BASETEN_API_KEY")
BASETEN_MODEL_SLUG = os.getenv("BASETEN_MODEL_SLUG")

if not BASETEN_API_KEY or not BASETEN_MODEL_SLUG:
    raise ValueError(
        "BASETEN_API_KEY and BASETEN_MODEL_SLUG must be set in your .env file.\n"
        "Example: BASETEN_MODEL_SLUG=deepseek-ai/DeepSeek-V3.1"
    )

baseten_llm = LLM(
    model=f"openai/{BASETEN_MODEL_SLUG}",
    base_url="https://inference.baseten.co/v1",
    api_key=BASETEN_API_KEY,
)


@tool("Web search")
def web_search_tool(query: str) -> str:
    """Deep research the web. Accepts any natural language research question and
    returns a synthesised answer with cited sources via You.com Research API."""
    return search_web(query)


@tool("SEC EDGAR search")
def edgar_search_tool(company_name: str) -> str:
    """Retrieve SEC EDGAR financial filing data for a public US company."""
    return search_filings(company_name)
