# Agent Tools

Short reference for the data-retrieval tools exposed to the Vantage research agent.
Every tool is a plain Python function; CrewAI wraps them via `@tool` in [root_agent.py](../root_agent.py).

---

## `search_filings(company_name, filing_type="10-K")` — SEC EDGAR

**Module:** [edgar_tool.py](edgar_tool.py)
**Library:** [edgartools](https://github.com/dgunning/edgartools)

Pulls real financial data on demand from SEC EDGAR for a public US company.

- Resolves `company_name` → ticker via `TICKER_TO_CIK` or a name map (Salesforce, HubSpot,
  Microsoft, Alphabet, Amazon, Apple, Meta, Oracle, SAP, ServiceNow).
- Calls `edgar.Company(ticker).get_financials()` to get the latest XBRL-parsed
  income statement and balance sheet.
- Calls `Company.get_filings(form=filing_type).latest()` for the citation URL.
- Returns a markdown block: filing header, income statement table, balance sheet table.
- Private or unknown company → `[PRIVATE OR NOT FOUND]` fallback message so the
  analyst can populate `financial_health.source = "N/A — private company"`.

edgartools uses a built-in local disk cache. Pre-warm demo tickers before a demo with:

```bash
python -m backend.scripts.prewarm_edgar
```

Identity for SEC's required `User-Agent` is taken from `EDGAR_IDENTITY` env var
(defaults to `"VantageAI team@vantage-ai.com"`).

---

## `search_web(query)` — You.com live web search

**Module:** [you_com_tool.py](you_com_tool.py)
**API:** [You.com Search API](https://api.ydc-index.io/search)

Live web search for news, pricing pages, job postings, reviews, executive bios,
funding announcements — anything not in SEC filings.

- Hits `https://api.ydc-index.io/search` with `YOU_COM_API_KEY` in the
  `X-API-Key` header.
- Returns the top 5 hits formatted as `Source: <url> / Title / Snippet` blocks.
- Timeouts and API errors surface as `[ERROR]` / `[NO RESULTS]` strings so the
  agent can degrade gracefully.

## `professional_first_look_search(company, year=None)` — curated First Look query

**Module:** [you_com_tool.py](you_com_tool.py)

Wraps `search_web` with an analyst-crafted query template that covers the full
competitive-intelligence surface in one call: recent news, financial
performance, product launches, executive changes, pricing strategy, G2/Capterra
reviews, hiring signals, funding/M&A, strategic risks.

Used as **step 1** in the First Look flow so the researcher has a broad baseline
before any targeted follow-up queries.

---

## How the crew consumes these tools

[root_agent.py](../root_agent.py) wraps each function with `@tool(...)` decorators
and attaches them to the `researcher` Agent:

```python
@tool("SEC EDGAR search")
def edgar_search_tool(company_name: str) -> str: ...

@tool("Web search")
def web_search_tool(query: str) -> str: ...

@tool("Professional First Look web search")
def first_look_search_tool(company: str) -> str: ...

researcher = Agent(tools=[first_look_search_tool, web_search_tool, edgar_search_tool], ...)
```

The `analyst` Agent has no tools — it only synthesises the researcher's output
into the final structured JSON report.

## Environment variables

| Variable | Used by | Required |
|---|---|---|
| `YOU_COM_API_KEY` | web search | yes (for web) |
| `EDGAR_IDENTITY` | EDGAR | no (has default) |
| `BASETEN_API_KEY`, `BASETEN_MODEL_SLUG` | LLM | yes (or OpenAI) |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | LLM fallback | no |
| `LLM_PROVIDER` | LLM selector (`baseten` / `openai`) | no |
