"""RR Finance Assist API, milestone 6.

Build the search index once:  python -m scripts.build_index
Run from the project folder:  uvicorn app.main:app --reload
Then open http://127.0.0.1:8000 (chat UI) or http://127.0.0.1:8000/docs (try /api/ask there).
"""
import json
from pathlib import Path
from typing import Literal, Optional

import openai
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from app import backend, rag, tools
from app.chat import ChatService
from app.logging_utils import log_event
from app.search import SearchService
from app.triage import TriageError, triage

app = FastAPI(title="RR Finance Assist", version="0.6")
chat = ChatService()
try:                                                     # new in milestone 5
    search = SearchService(chat.client)
    tools.set_search_service(search)
except Exception as e:                                   # no index yet: keep running with keyword fallback
    search = None
    log_event(level="warning", event="search_unavailable", detail=str(e)[:200])
WEB = Path(__file__).resolve().parent.parent / "web"


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    message: str = Field(min_length=1, max_length=4000)
    # DEMO ONLY: the UI says who is "signed in". A real app takes the customer from a verified
    # sign-in token on the server (Module 10), never from a field the browser can change.
    customer_id: Optional[str] = None


class ResetRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class TriageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@app.get("/")
def home():
    return FileResponse(WEB / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/demo-customers")
def demo_customers():
    """New in milestone 4: the fictional customers the demo UI can 'sign in' as."""
    return [{"customer_id": k, "name": v["name"]} for k, v in backend.CUSTOMERS.items()]


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """Stream the answer as server-sent events: one `data: {json}` line per event."""
    if req.customer_id is not None and req.customer_id not in backend.CUSTOMERS:
        raise HTTPException(status_code=400, detail="Unknown customer.")

    def events():
        for event in chat.stream(req.session_id, req.message, customer_id=req.customer_id):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/reset")
def reset(req: ResetRequest):
    chat.reset(req.session_id)
    return {"status": "reset"}


@app.get("/api/search")
def search_endpoint(q: str = Query(min_length=2, max_length=200), kind: Literal["product", "help"] = "product",
                    family: Optional[Literal["accounts", "cards", "loans"]] = None,
                    max_annual_fee_usd: Optional[int] = Query(default=None, ge=0),
                    k: int = Query(default=5, ge=1, le=20)):
    """New in milestone 5: semantic + keyword (hybrid) search over products or help-centre sections."""
    if search is None:
        raise HTTPException(status_code=503, detail="Search index not built. Run: python -m scripts.build_index")
    try:
        hits = search.search(q, k=k, kind=kind, family=family, max_annual_fee_usd=max_annual_fee_usd)
    except openai.APIError as e:
        log_event(level="error", event="search_api_error", error=type(e).__name__)
        raise HTTPException(status_code=503, detail="The embedding service is unavailable. Please try again shortly.")
    return {"query": q, "kind": kind, "results": [
        {k_: h.get(k_) for k_ in ("id", "title", "score", "source", "family", "annual_fee_usd")} | {"text": h["text"][:300]}
        for h in hits]}


@app.post("/api/ask")
def ask_endpoint(req: AskRequest):
    """New in milestone 6: one question, one answer from the help centre, with checked citations."""
    if search is None:
        raise HTTPException(status_code=503, detail="Search index not built. Run: python -m scripts.build_index")
    try:
        result = rag.ask(chat.client, search, req.question)
    except openai.APIError as e:
        log_event(level="error", event="ask_api_error", error=type(e).__name__)
        raise HTTPException(status_code=503, detail="The AI service is unavailable. Please try again shortly.")
    log_event(level="warning" if result.get("unknown_citations") or result.get("related") else "info",
              event="ask", found=result["found"], uncited=bool(result.get("related")),
              sources=[s["n"] for s in result["sources"]], unknown_citations=result.get("unknown_citations"),
              prompt_version=result["prompt_version"])
    return result


@app.post("/api/triage")
def triage_endpoint(req: TriageRequest):
    """Classify a customer message into validated JSON for routing (structured outputs since milestone 4)."""
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
