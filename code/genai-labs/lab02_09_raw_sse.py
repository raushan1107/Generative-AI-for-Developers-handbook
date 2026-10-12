"""Drill 02.9: look at the raw server-sent events (SSE) behind streaming."""
import os

import requests
from dotenv import load_dotenv

load_dotenv()

url = os.environ["AZURE_OPENAI_BASE_URL"].rstrip("/") + "/chat/completions"
headers = {"api-key": os.environ["AZURE_OPENAI_API_KEY"], "Content-Type": "application/json"}
body = {
    "model": os.getenv("AZURE_OPENAI_DEPLOYMENT", "chat"),
    "messages": [{"role": "user", "content": "Name three cloud providers, comma separated."}],
    "stream": True,
}

with requests.post(url, headers=headers, json=body, stream=True, timeout=60) as resp:
    print("HTTP", resp.status_code, "·", resp.headers.get("content-type"), "\n")
    for line in resp.iter_lines(decode_unicode=True):
        if line:                      # events are separated by blank lines
            print(line[:140])
