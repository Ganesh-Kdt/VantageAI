import os
from dotenv import load_dotenv
from youdotcom import You

load_dotenv()

YOU_COM_API_KEY = os.getenv("YOU_COM_API_KEY")


def search_web(query: str) -> str:
    """
    Deep research the web for competitive intelligence about a company.
    Uses You.com Search API to return web results with cited sources.

    Args:
        query: Research question or topic, e.g.
               "Salesforce revenue growth and financial health 2024" or
               "HubSpot hiring trends and headcount changes 2024"

    Returns:
        Synthesised research results with inline source citations.
    """
    if not YOU_COM_API_KEY:
        return "[ERROR] YOU_COM_API_KEY not set in environment."

    try:
        with You(api_key_auth=YOU_COM_API_KEY) as you:
            results = you.search.unified(query=query, count=5)

        if not (results and results.results and results.results.web):
            return f"[NO RESULTS] No web results found for: {query}"

        formatted = []
        for result in results.results.web:
            title = result.title or "No title"
            url = result.url or ""
            snippet = result.description or (result.snippets[0] if result.snippets else "")
            formatted.append(f"Source: {url}\nTitle: {title}\nSnippet: {snippet}\n")

        return "\n".join(formatted)

    except Exception as e:
        if "403 Forbidden" in str(e):
            return (
                "[ERROR] You.com search failed with 403 Forbidden. This likely means your "
                "YOU_COM_API_KEY is invalid, has expired, or your account has usage limit issues. "
                "Please check your You.com developer dashboard."
            )
        return f"[ERROR] You.com search failed: {str(e)}"
