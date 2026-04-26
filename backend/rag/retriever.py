"""
RAG Retriever — finds the most relevant chunks from cached SEC filings.
Called by edgar_tool.py when a company's data has been pre-embedded.
"""
import os
import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
EMBEDDING_MODEL = "text-embedding-3-small"

# In-memory cache so we don't re-load JSON on every query
_loaded_stores: dict = {}


def _load_store(ticker: str) -> dict | None:
    """Load a company's embedding store from disk (cached in memory)."""
    ticker = ticker.upper()
    if ticker in _loaded_stores:
        return _loaded_stores[ticker]

    cache_path = os.path.join(CACHE_DIR, f"{ticker}.json")
    if not os.path.exists(cache_path):
        return None

    with open(cache_path) as f:
        store = json.load(f)

    # Convert embeddings back to numpy for fast dot product
    store["embeddings_np"] = np.array(store["embeddings"])
    _loaded_stores[ticker] = store
    return store


def retrieve_from_cache(ticker: str, query: str = None, top_k: int = 4) -> str | None:
    """
    Retrieve the most relevant filing chunks for a query.

    Args:
        ticker: Company ticker e.g. "CRM"
        query: Natural language query to match against. If None, returns
               a general summary of the top chunks.
        top_k: Number of chunks to return

    Returns:
        Concatenated relevant chunks with citation info, or None if not cached.
    """
    store = _load_store(ticker)
    if not store:
        return None

    chunks = store["chunks"]
    embeddings = store["embeddings_np"]
    metadata = store.get("metadata", {})

    # Validate filing date from metadata to prevent issues with bad cache data
    filing_date_str = metadata.get("filing_date", "date unknown")
    try:
        if filing_date_str != "date unknown":
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
            if filing_date > datetime.now():
                filing_date_str = "date unknown"  # Reset if date is in the future
    except (ValueError, TypeError):
        filing_date_str = "date unknown"

    if query:
        # Embed the query and find most similar chunks
        response = client.embeddings.create(
            input=[query],
            model=EMBEDDING_MODEL,
        )
        query_embedding = np.array(response.data[0].embedding)

        # Cosine similarity via dot product (embeddings are normalised)
        scores = embeddings @ query_embedding
        top_indices = np.argsort(scores)[-top_k:][::-1]
        selected_chunks = [chunks[i] for i in top_indices]
    else:
        # No query — just return the first few chunks as a summary
        selected_chunks = chunks[:top_k]

    filing_ref = (
        f"SEC {metadata.get('filing_type', '10-K')} "
        f"filed {filing_date_str} — "
        f"{metadata.get('url', 'see SEC EDGAR')}"
    )

    result = f"[CITATION: {filing_ref}]\n\n"
    result += "\n\n---\n\n".join(selected_chunks)
    return result


def list_cached_companies() -> list[str]:
    """Return tickers that have been pre-cached."""
    if not os.path.exists(CACHE_DIR):
        return []
    return [
        f.replace(".json", "")
        for f in os.listdir(CACHE_DIR)
        if f.endswith(".json")
    ]
