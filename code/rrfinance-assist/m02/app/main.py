"""RR Finance Assist API, milestone 2.

Run from the project folder:  uvicorn app.main:app --reload
Then open http://127.0.0.1:8000 (chat UI) or http://127.0.0.1:8000/docs (API docs).
"""
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.chat import ChatService

app = FastAPI(title="RR Finance Assist", version="0.2")
chat = ChatService()
WEB = Path(__file__).resolve().parent.parent / "web"


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    message: str = Field(min_length=1, max_length=4000)


class ResetRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)


@app.get("/")
def home():
    return FileResponse(WEB / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """Stream the answer as server-sent events: one `data: {json}` line per event."""
    def events():
        for event in chat.stream(req.session_id, req.message):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/reset")
def reset(req: ResetRequest):
    chat.reset(req.session_id)
    return {"status": "reset"}
