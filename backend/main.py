import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from backend.agent.root_agent import (
    build_first_look_crew,
)

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

# ── Request/Response models ───────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    company: str

# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """
    First Look — full cited intelligence report for a single company.
    ~90 seconds for live analysis, instant for demo-cached companies.
    """
    try:
        crew = build_first_look_crew(req.company)
        result = crew.kickoff()
        report = _parse_json_response(str(result))
        return {"source": "live", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
