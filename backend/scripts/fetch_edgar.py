"""
Pre-fetch and embed SEC EDGAR filings for demo companies.
Run this BEFORE the hackathon to ensure fast demo responses.

Usage:
    python -m backend.scripts.fetch_edgar
"""
import os
import requests
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from backend.rag.embedder import embed_and_store

USER_AGENT = "VantageAI team@vantage-ai.com"

DEMO_COMPANIES = {
    "CRM": {
        "name": "Salesforce",
        "cik": "0001108524",
        "filing_type": "10-K",
    },
    "HUBS": {
        "name": "HubSpot",
        "cik": "0001404655",
        "filing_type": "10-K",
    },
}


def fetch_filing_text(cik: str, filing_type: str = "10-K") -> tuple[str, dict]:
    """Fetch the most recent filing text from EDGAR."""
    print(f"  Fetching submissions for CIK {cik}...")
    submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(
        submissions_url,
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accession_numbers = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])

    for i, form in enumerate(forms):
        if form == filing_type:
            accession = accession_numbers[i]
            date = filing_dates[i]
            accession_clean = accession.replace("-", "")

            # Get the filing index to find the actual document
            index_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{int(cik)}/{accession_clean}/{accession}-index.json"
            )
            try:
                index_resp = requests.get(
                    index_url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=10,
                )
                index_data = index_resp.json()
                files = index_data.get("directory", {}).get("item", [])

                # Find the main .htm document
                for file_info in files:
                    name = file_info.get("name", "")
                    if name.endswith(".htm") and filing_type.lower() in name.lower():
                        doc_url = (
                            f"https://www.sec.gov/Archives/edgar/data/"
                            f"{int(cik)}/{accession_clean}/{name}"
                        )
                        print(f"  Downloading: {doc_url}")
                        doc_resp = requests.get(
                            doc_url,
                            headers={"User-Agent": USER_AGENT},
                            timeout=30,
                        )
                        # Strip HTML tags (basic)
                        text = _strip_html(doc_resp.text)
                        metadata = {
                            "filing_type": filing_type,
                            "filing_date": date,
                            "accession": accession,
                            "url": doc_url,
                        }
                        return text, metadata
            except Exception as e:
                print(f"  Warning: Could not fetch filing document: {e}")
                # Return a stub so embedding doesn't fail
                stub = (
                    f"{filing_type} filing for CIK {cik}, filed {date}. "
                    f"Manual download required from SEC EDGAR. "
                    f"Accession number: {accession}"
                )
                return stub, {"filing_type": filing_type, "filing_date": date}

    return "", {}


def _strip_html(html: str) -> str:
    """Very basic HTML tag stripping."""
    import re
    # Remove script/style blocks
    html = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", "", html, flags=re.DOTALL)
    # Remove all remaining tags
    html = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    html = re.sub(r"\s+", " ", html).strip()
    return html


if __name__ == "__main__":
    print("=== Vantage AI — Pre-fetching demo company filings ===\n")

    for ticker, info in DEMO_COMPANIES.items():
        print(f"\n[{ticker}] {info['name']}")
        try:
            text, metadata = fetch_filing_text(info["cik"], info["filing_type"])
            if text:
                embed_and_store(ticker, text, metadata)
                print(f"  ✓ {ticker} cached successfully")
            else:
                print(f"  ✗ No filing text retrieved for {ticker}")
        except Exception as e:
            print(f"  ✗ Failed for {ticker}: {e}")

    print("\n=== Done. Run health check: curl http://localhost:8000/health ===")
