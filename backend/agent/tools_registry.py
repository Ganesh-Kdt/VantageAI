import os
from dotenv import load_dotenv
from crewai import LLM
from crewai.tools import tool
from backend.agent.tools.you_com_tool import search_web
from backend.resolve_ticker import search_companies_for_dropdown
from backend.edgar_ingest import run_rag_pipeline

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


@tool("SEC EDGAR Search Tool")
def edgar_search_tool(company_name: str) -> str:
    """
    Searches a company's latest SEC 10-K filings to answer specific financial or risk-related queries.
    Pass the company name and the specific question you want answered.
    """
    # 1. Resolve the company name to a Ticker
    matches = search_companies_for_dropdown(company_name, limit=1)
    if not matches:
        return f"Could not find SEC ticker for company: {company_name}. They may be private."
    
    ticker = matches[0]['ticker']
    
    # 2. Run your Pinecone/Mistral RAG pipeline
    try:
        rag_result = run_rag_pipeline(company_name, ticker)
        return rag_result
    except Exception as e:
        return f"Error retrieving data for {ticker}: {str(e)}"
