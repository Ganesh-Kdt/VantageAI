"""Quick test — confirms Baseten Model API connection works.
Run from veris/: python test_baseten.py
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://inference.baseten.co/v1",
    api_key=os.getenv("BASETEN_API_KEY"),
)

response = client.chat.completions.create(
    model=os.getenv("BASETEN_MODEL_SLUG"),
    messages=[{"role": "user", "content": "Say hello in one sentence."}],
    max_tokens=50,
)

print("Baseten response:", response.choices[0].message.content)
