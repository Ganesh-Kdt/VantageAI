"""
Pre-warm the edgartools local cache for demo tickers.

Run this once before a demo to avoid the first-call cold latency on stage.
edgartools caches on disk, so subsequent search_filings() calls are fast.

Usage:
    python -m backend.scripts.prewarm_edgar
"""
from backend.agent.tools.edgar_tool import TICKER_TO_CIK, search_filings

DEMO_TICKERS = list(TICKER_TO_CIK.keys())


def main() -> None:
    for ticker in DEMO_TICKERS:
        print(f"[warm] {ticker} ...", flush=True)
        result = search_filings(ticker)
        status = "OK" if result.startswith("[SEC") else "FAIL"
        print(f"[warm] {ticker}: {status} ({len(result)} chars)")


if __name__ == "__main__":
    main()
