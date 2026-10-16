"""Module 06: the RAG pipeline in one function, built from this module's helpers.
retrieve (with a relevance floor) -> nothing relevant? stop, no model call -> build the prompt
-> generate -> NOT_FOUND? say so -> check the citations."""
import os

import openai

from citations import check
from embed import EMBED_MODEL
from kb_index import load_or_build
from llm import MODEL, get_client
from rag_prompt import NOT_FOUND, build_messages

# Relevance floor on cosine similarity. Model-specific: calibrate it for yours with Drill 06.6.
FLOORS = {"nomic-embed-text": 0.55, "text-embedding-3-small": 0.30, "text-embedding-3-large": 0.30}
MIN_SCORE = float(os.getenv("RAG_MIN_SCORE") or FLOORS.get(EMBED_MODEL, 0.30))
NO_ANSWER = "I couldn't find that in RR Finance Bank's documents. Shall I raise a case for the support team?"


def generate(client, messages):
    """Low temperature for factual answers; some reasoning models reject the parameter, so retry without."""
    try:
        return client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
    except openai.BadRequestError:
        return client.chat.completions.create(model=MODEL, messages=messages)


def answer(question: str, audience=("public",), index=None, client=None, k: int = 4) -> dict:
    index = index or load_or_build()
    hits = index.search(question, k=k, audience=audience, min_score=MIN_SCORE)
    if not hits:                                             # nothing relevant: don't let the model improvise
        return {"answer": NO_ANSWER, "found": False, "sources": [], "report": None, "llm_calls": 0}
    messages, sources = build_messages(question, hits)
    response = generate(client or get_client(), messages)
    text = (response.choices[0].message.content or "").strip()
    if not text or text.startswith(NOT_FOUND):
        return {"answer": NO_ANSWER, "found": False, "sources": sources, "report": None, "llm_calls": 1}
    return {"answer": text, "found": True, "sources": sources, "report": check(text, sources, question), "llm_calls": 1}
