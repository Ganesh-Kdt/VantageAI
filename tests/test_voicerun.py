"""Quick test — confirms VoiceRun TTS is wired correctly.
Run from veris/: python test_voicerun.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

r = requests.post(
    "https://api.voicerun.ai/v1/tts",
    headers={"Authorization": f"Bearer {os.getenv('VOICERUN_API_KEY')}"},
    json={"text": "Vantage competitive intelligence is ready.", "voice": "nova"},
    timeout=15,
)

if r.ok:
    with open("test_output.mp3", "wb") as f:
        f.write(r.content)
    print("Saved test_output.mp3 — play it to confirm VoiceRun works")
else:
    print(f"Error {r.status_code}: {r.text}")
