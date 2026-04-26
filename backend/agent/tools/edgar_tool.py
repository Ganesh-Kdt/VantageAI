"""
SEC EDGAR tool — pulls real financial data on demand via edgartools.

Returns a markdown-formatted block with the latest income statement, balance
sheet, and a citation link for the filing. Built-in edgartools caching makes
repeat calls fast; for demo safety, warm the cache ahead of time with
`backend/scripts/prewarm_edgar.py`.
"""
from __future__ import annotations

import os

from edgar import Company, set_identity

# SEC requires a contact identity on every request.
set_identity(os.getenv("EDGAR_IDENTITY", "VantageAI team@vantage-ai.com"))

# Preserve the ticker map — the orchestrator imports it to seed known_tickers.
TICKER_TO_CIK = {
    "CRM": "0001108524",   # Salesforce
    "HUBS": "0001404655",  # HubSpot
    "MSFT": "0000789019",  # Microsoft
    "GOOGL": "0001652044", # Alphabet
    "AMZN": "0001018724",  # Amazon
    "AAPL": "0000320193",  # Apple
    "META": "0001326801",  # Meta
    "ORCL": "0001341439",  # Oracle
    "SAP": "0000723254",   # SAP
    "NOW": "0001373715",   # ServiceNow
}

# Reverse map for name-based lookup fallback.
_NAME_TO_TICKER = {
    "salesforce": "CRM",
    "hubspot": "HUBS",
    "microsoft": "MSFT",
    "alphabet": "GOOGL",
    "google": "GOOGL",
    "amazon": "AMZN",
    "apple": "AAPL",
    "meta": "META",
    "facebook": "META",
    "oracle": "ORCL",
    "sap": "SAP",
    "servicenow": "NOW",
}


def _resolve_ticker(company_name: str) -> str | None:
    key = company_name.strip().upper()
    if key in TICKER_TO_CIK:
        return key
    return _NAME_TO_TICKER.get(company_name.strip().lower())


def search_filings(company_name: str, filing_type: str = "10-K") -> str:
    """
    Retrieve SEC EDGAR financial data for a public US company.

    Returns the latest income statement + balance sheet as markdown, plus a
    citation link to the filing on sec.gov. For private companies, returns a
    clear 'not found' message so the analyst can note it in the report.

    Args:
        company_name: Company name or ticker, e.g. "Salesforce" or "CRM".
        filing_type:  "10-K" (annual), "10-Q" (quarterly), "8-K" (material).

    Returns:
        A markdown block suitable to paste directly into the analyst context.
    """
    ticker = _resolve_ticker(company_name)
    if not ticker:
        return (
            f"[PRIVATE OR NOT FOUND] No SEC EDGAR filings matched '{company_name}'. "
            f"Likely a private company. Note 'N/A — private company' in "
            f"financial_health.source and rely on web sources."
        )

    try:
        company = Company(ticker)
        financials = company.get_financials()
        filings = company.get_filings(form=filing_type)
        latest = filings.latest()

        parts = [
            f"[SEC {filing_type} — {company.name} ({ticker}, CIK {company.cik})]",
            f"Filed: {latest.filing_date}",
            f"Source: {latest.homepage_url}",
            "",
        ]

        if financials is not None:
            income = financials.income_statement()
            balance = financials.balance_sheet()
            if income is not None:
                parts.append("### Income Statement")
                parts.append(income.to_markdown()[:3500])
                parts.append("")
            if balance is not None:
                parts.append("### Balance Sheet")
                parts.append(balance.to_markdown()[:3500])
                parts.append("")
        else:
            parts.append("[No structured financials available for this issuer.]")

        return "\n".join(parts)

    except Exception as e:
        return (
            f"[ERROR] Failed to fetch EDGAR data for {company_name} ({ticker}): "
            f"{type(e).__name__}: {e}"
        )
