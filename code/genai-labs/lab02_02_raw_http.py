"""Drill 02.2: one chat call with plain HTTP, to see exactly what the SDK hides."""
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

url = os.environ["AZURE_OPENAI_BASE_URL"].rstrip("/") + "/chat/completions"
headers = {
    "api-key": os.environ["AZURE_OPENAI_API_KEY"],  # Azure's key header
    "Content-Type": "application/json",
}
body = {
    "model": os.getenv("AZURE_OPENAI_DEPLOYMENT", "chat"),
    "messages": [
        {"role": "system", "content": "You are Traincrest Assist, TrainCrest's learner-support assistant. Be brief."},
        {"role": "user", "content": "What does 'batch confirmed' mean on my enrolment?"},
    ],
}

start = time.perf_counter()
resp = requests.post(url, headers=headers, json=body, timeout=60)
print(f"HTTP {resp.status_code} in {time.perf_counter() - start:.2f}s\n")

for name in ("x-request-id", "apim-request-id", "x-ratelimit-remaining-requests", "x-ratelimit-remaining-tokens"):
    if name in resp.headers:
        print(f"{name}: {resp.headers[name]}")

data = resp.json()
print("\n" + json.dumps(data, indent=2, ensure_ascii=False))
Path("response.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("\nSaved the response body to response.json")
