import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv
from backend.agent.root_agent import (
    build_first_look_crew,
    build_head_to_head_crew,
    build_digest_crew,
)
from backend.agent.prompts import HEAD_TO_HEAD_PROMPT, DIGEST_PROMPT

load_dotenv()

app = FastAPI(
    title="Vantage AI",
    description="Competitive intelligence co-pilot for startups",
    version="0.1.0",
)

# Allow all origins for hackathon — tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Demo cache (fallback if APIs are slow during demo) ────────────────────────
DEMO_CACHE_DIR = os.path.join(os.path.dirname(__file__), "scripts", "demo_cache")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"


def load_demo_cache(company: str) -> dict | None:
    path = os.path.join(DEMO_CACHE_DIR, f"{company.lower().replace(' ', '_')}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


# ── Request/Response models ───────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    company: str
    mode: str = "first_look"   # first_look | head_to_head | digest
    demo: bool = False          # Force demo cache


class HeadToHeadRequest(BaseModel):
    company_a: str
    company_b: str
    demo: bool = False


class DigestRequest(BaseModel):
    companies: list[str]       # List of companies to monitor
    demo: bool = False


class TTSRequest(BaseModel):
    text: str


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "cached_companies": [],
        "demo_mode": DEMO_MODE,
    }


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """
    First Look — full cited intelligence report for a single company.
    ~90 seconds for live analysis, instant for demo-cached companies.
    """
    # Serve from demo cache if forced or in demo mode
    if req.demo or DEMO_MODE:
        cached = load_demo_cache(req.company)
        if cached:
            return {"source": "demo_cache", "report": cached}

    try:
        crew = build_first_look_crew(req.company)
        result = crew.kickoff()
        report = _parse_json_response(str(result))
        return {"source": "live", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/head-to-head")
def head_to_head(req: HeadToHeadRequest):
    """
    Head to Head — side-by-side comparison of two companies.
    """
    if req.demo or DEMO_MODE:
        cached = load_demo_cache(f"{req.company_a}_vs_{req.company_b}")
        if cached:
            return {"source": "demo_cache", "comparison": cached}

    try:
        crew = build_head_to_head_crew(req.company_a, req.company_b)
        result = crew.kickoff()
        comparison = _parse_json_response(str(result))
        return {"source": "live", "comparison": comparison}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/digest")
def generate_digest(req: DigestRequest):
    """
    Always On — weekly competitive digest for a list of monitored companies.
    """
    if req.demo or DEMO_MODE:
        cached = load_demo_cache("weekly_digest")
        if cached:
            return {"source": "demo_cache", "digest": cached}

    try:
        crew = build_digest_crew(req.companies)
        result = crew.kickoff()
        digest = _parse_json_response(str(result))
        return {"source": "live", "digest": digest}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tts")
def text_to_speech(req: TTSRequest):
    """Cartesia TTS — returns WAV audio of the given text using Brooke's voice."""
    cartesia_key = os.getenv("CARTESIA_API_KEY")
    if not cartesia_key:
        raise HTTPException(status_code=500, detail="CARTESIA_API_KEY not set")

    try:
        r = httpx.post(
            "https://api.cartesia.ai/tts/bytes",
            headers={
                "X-API-Key": cartesia_key,
                "Cartesia-Version": "2024-06-10",
                "Content-Type": "application/json",
            },
            json={
                "model_id": "sonic-2",
                "transcript": req.text,
                "voice": {"mode": "id", "id": "e07c00bc-4134-4eae-9ea4-1a55fb45746b"},
                "output_format": {
                    "container": "wav",
                    "encoding": "pcm_s16le",
                    "sample_rate": 44100,
                },
            },
            timeout=30,
        )
        r.raise_for_status()
        return Response(content=r.content, media_type="audio/wav")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Cartesia error: {e.response.text}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, stripping markdown fences if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])  # Strip ``` fences
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Return raw text if JSON parsing fails
        return {"raw": text, "parse_error": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
