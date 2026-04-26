import os
import requests
from primfunctions.events import Event, StartEvent, TextEvent, StopEvent, TextToSpeechEvent
from primfunctions.context import Context

BACKEND_URL = os.getenv("VANTAGE_BACKEND_URL", "http://localhost:8000")

BROOKE_VOICE = {
    "provider": "cartesia",
    "identifier": "e07c00bc-4134-4eae-9ea4-1a55fb45746b",
}


async def handler(event: Event, context: Context):
    if isinstance(event, StartEvent):
        yield TextToSpeechEvent(
            text="Welcome to Vantage. Which company would you like to research?",
            voice=BROOKE_VOICE,
            interruptible=True,
        )

    elif isinstance(event, TextEvent):
        company = event.data.get("text", "").strip()
        if not company:
            return

        yield TextToSpeechEvent(
            text=f"Got it — researching {company} now. This takes about 90 seconds.",
            voice=BROOKE_VOICE,
        )

        try:
            response = requests.post(
                f"{BACKEND_URL}/analyze",
                json={"company": company, "mode": "first_look"},
                timeout=120,
            )
            response.raise_for_status()
            report = response.json().get("report", {})
            summary = report.get("strategic_summary", "Research complete.")

            yield TextToSpeechEvent(
                text=summary,
                voice=BROOKE_VOICE,
                interruptible=True,
            )

            yield TextToSpeechEvent(
                text="Would you like to research another company or ask a follow-up question?",
                voice=BROOKE_VOICE,
            )

        except Exception:
            yield TextToSpeechEvent(
                text="I had trouble reaching the research engine. Please try again.",
                voice=BROOKE_VOICE,
            )

    elif isinstance(event, StopEvent):
        yield TextToSpeechEvent(
            text="Thanks for using Vantage. Goodbye!",
            voice=BROOKE_VOICE,
        )
