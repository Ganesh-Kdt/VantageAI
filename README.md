# Vantage AI 🔍

> Competitive intelligence co-pilot for startups — cited, grounded, voice-first.

Built at **Enterprise Agent Jam NYC** in 6 hours.

---

## What it does

Vantage gives any startup the competitive intelligence edge that used to cost $40k/year.
Type a competitor name. Get a cited, risk-scored intelligence brief in ~90 seconds.
---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Agent orchestration | **CrewAI** — role-based researcher + analyst crew, sequential tasks |
| Live web search | **You.com Search API** — news, job posts, G2 reviews, pricing |
| Financial filings | **SEC EDGAR** — 10-K, 10-Q, 8-K (fetch + truncate, no RAG) |
| LLM inference | **Baseten** — open-source model, direct API (no LiteLLM) |
| Voice I/O | **VoiceRun** — STT input, TTS output |
| Agent testing | **Veris AI** — simulation & edge case testing |
| Frontend | React |
| Backend | FastAPI + Python |

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_ORG/vantage-ai.git
cd vantage-ai/veris

# Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in your API keys in .env
```

Required keys:
- `BASETEN_API_KEY` — from [baseten.co](https://baseten.co)
- `BASETEN_MODEL_SLUG` — your deployed model's slug, e.g. `deepseek-ai/DeepSeek-V3.1`. The code uses this to construct the API endpoint.
- `YOU_COM_API_KEY` — from [you.com/api](https://you.com/api)
- `VOICERUN_API_KEY` — from VoiceRun dashboard
- `OPENAI_API_KEY` — from openai.com, required for pre-caching demo data.


### 3. Run

```bash
# Terminal 1 — Backend (run from veris/)
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm start
```

App runs at `http://localhost:3000`. API at `http://localhost:8000`.

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check + cached companies list |
| `POST` | `/analyze` | First Look — single company report |
| `POST` | `/head-to-head` | Compare two companies |
| `POST` | `/digest` | Weekly competitive digest |

Add `"demo": true` to any request body to serve pre-cached data instantly.

---

## Project structure

```
veris/
├── backend/
│   ├── agent/
│   │   ├── root_agent.py       CrewAI crew, agents, and task definitions
│   │   ├── prompts.py          System prompts for all modes
│   │   └── tools/
│   │       ├── you_com_tool.py You.com search tool
│   │       └── edgar_tool.py   SEC EDGAR filing tool
│   ├── rag/
│   │   ├── embedder.py         (kept, not in main request path)
│   │   └── retriever.py        (kept, not in main request path)
│   ├── scripts/
│   │   └── demo_cache/         Pre-generated demo responses (gitignored)
│   └── main.py                 FastAPI server
├── frontend/
│   └── src/
│       ├── App.jsx             Main app + mode routing
│       ├── components/
│       │   ├── CompanySearch   Search input + demo button
│       │   ├── ReportView      Full report with risk scores + citations
│       │   ├── HeadToHead      Two-company comparison input
│       │   ├── DigestView      Weekly digest display
│       │   └── VoiceButton     VoiceRun STT/TTS + browser fallback
│       └── api/index.js        Axios API helpers
├── veris/
│   └── veris.yaml              Simulation scenarios
├── .env.example
├── requirements.txt
└── README.md
```

---

*Built at Enterprise Agent Jam NYC — April 2026*
