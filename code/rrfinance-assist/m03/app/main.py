"""RR Finance Assist API, milestone 3.

Run from the project folder:  uvicorn app.main:app --reload
Then open http://127.0.0.1:8000 (chat UI) or http://127.0.0.1:8000/docs (try /api/triage there).
"""
import json
from pathlib import Path

import openai
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.chat import ChatService
from app.logging_utils import log_event
from app.triage import TriageError, triage

app = FastAPI(title="RR Finance Assist", version="0.3")
chat = ChatService()
WEB = Path(__file__).resolve().parent.parent / "web"


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    message: str = Field(min_length=1, max_length=4000)


class ResetRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)


class TriageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


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


@app.post("/api/triage")
def triage_endpoint(req: TriageRequest):
    """New in milestone 3: classify a customer message into validated JSON for routing."""
    try:
        result, version, attempts = triage(chat.client, req.message)
    except TriageError as e:
        log_event(level="warning", event="triage_failed", detail=str(e)[:200])
        raise HTTPException(status_code=502, detail="Could not triage this message. Please try again.")
    except openai.APIError as e:
        log_event(level="error", event="triage_api_error", error=type(e).__name__)
        raise HTTPException(status_code=503, detail="The AI service is unavailable. Please try again shortly.")
    log_event(level="info", event="triage", prompt_version=version, attempts=attempts,
              category=result.issue_category, urgency=result.urgency)
    return {"result": result.model_dump(), "prompt_version": version, "attempts": attempts}
