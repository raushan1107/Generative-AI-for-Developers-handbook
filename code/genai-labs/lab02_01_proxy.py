"""Drill 02.1 (reference solution): a backend between the browser and the model,
so the API key never leaves the server.

Run:  uvicorn lab02_01_proxy:app --reload     then open http://127.0.0.1:8000
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from llm import get_client, MODEL

app = FastAPI(title="Drill 02.1 · backend proxy")
client = get_client()  # the key is read from .env on the server only


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@app.get("/")
def page():
    return FileResponse(Path(__file__).with_name("lab02_01_index.html"))


@app.post("/api/ask")
def ask(q: Question):
    r = client.chat.completions.create(model=MODEL, messages=[
        {"role": "system", "content": "You help RR Finance Bank customers. Be brief and friendly."},
        {"role": "user", "content": q.question},
    ])
    return {"answer": r.choices[0].message.content}
