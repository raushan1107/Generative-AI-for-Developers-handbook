"""Retrieval-augmented generation over the help centre (milestone 6).

Used in two ways:
- the search_help tool in chat: the model decides when to look something up (tools.py);
- POST /api/ask: a fixed pipeline for the help-centre search box: retrieve -> prompt -> generate -> check.
Both number the sections they retrieve, so answers can cite them like [1], and both check the
citations in code before the customer sees them."""
import re

from app.config import HELP_CENTRE_URL, MODEL, RAG_MAX_CONTEXT_TOKENS, RAG_MIN_SCORE, RAG_TOP_K
from app.prompts import render

NOT_FOUND = "NOT_FOUND"
NO_ANSWER = ("I couldn't find that in the RR Finance Bank help centre. "
             "Would you like me to raise a case for our support team?")
SOURCE_TAG = re.compile(r"</?\s*sources?\b[^>]*>", re.I)
CITE = re.compile(r"\[(\d+)\]")


def approx_tokens(text: str) -> int:
    """About 4 characters per token in English: close enough for a budget, and needs no tokenizer download."""
    return len(text) // 4 + 1


def retrieve(search, question: str, k: int = RAG_TOP_K, min_score: float | None = None):
    """Help-centre sections for the question, best first. Below the relevance floor means 'not relevant'.
    The local index reports cosine; Azure AI Search hybrid scores aren't similarities, so no floor there."""
    min_score = RAG_MIN_SCORE if min_score is None else min_score
    hits = search.search(question, k=k, kind="help")
    return [h for h in hits if h.get("cosine") is None or h["cosine"] >= min_score]


def number_sources(hits, start: int = 1, max_tokens: int = RAG_MAX_CONTEXT_TOKENS):
    """Give each hit a citation number, keeping whole sections, best first, while they fit the budget."""
    sources, used = [], 0
    for h in hits:
        cost = approx_tokens(h["text"])
        if used + cost > max_tokens:
            continue
        used += cost
        sources.append({"n": start + len(sources), "id": h["id"], "title": h["title"],
                        "source": h["source"], "text": h["text"]})
    return sources


def format_sources(sources) -> str:
    """Numbered <source> blocks. A section can't close the tag early and smuggle in 'instructions'."""
    return "\n\n".join(f'<source id="{s["n"]}" title="{s["title"]}">\n{SOURCE_TAG.sub("", s["text"])}\n</source>'
                       for s in sources)


def public(source: dict) -> dict:
    """What the browser gets for a cited source: number, title and a link, not the internal text."""
    return {"n": source["n"], "title": source["title"],
            "url": HELP_CENTRE_URL + source["source"].removesuffix(".md")}


def check_citations(answer: str, sources):
    """Return (answer, cited_sources, unknown_numbers). Citations to sources the model never saw are removed."""
    known = {s["n"]: s for s in sources}
    cited, unknown = [], []
    for n in map(int, CITE.findall(answer)):
        if n in known and known[n] not in cited:
            cited.append(known[n])
        elif n not in known and n not in unknown:
            unknown.append(n)
    if unknown:
        answer = CITE.sub(lambda m: m.group(0) if int(m.group(1)) in known else "", answer)
        answer = re.sub(r"[ \t]+([.,;!?])", r"\1", answer)
    return answer, cited, unknown


def ask(client, search, question: str) -> dict:
    """The help-centre box: one question in, a grounded answer with its sources out."""
    sources = number_sources(retrieve(search, question))
    if not sources:                                          # nothing relevant: no model call, no improvising
        return {"answer": NO_ANSWER, "found": False, "sources": [], "prompt_version": None}
    system, version = render("rag_answer")
    user = f"<sources>\n{format_sources(sources)}\n</sources>\n\nQuestion: {question}"
    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    text = (response.choices[0].message.content or "").strip()
    if not text or text.startswith(NOT_FOUND):
        return {"answer": NO_ANSWER, "found": False, "sources": [], "prompt_version": version}
    text, cited, unknown = check_citations(text, sources)
    # Small models sometimes answer correctly but cite nothing. Don't pretend they did: list what was
    # retrieved as "related" instead, and log it (Module 09 measures the citation rate).
    related = [] if cited else [public(s) for s in sources[:2]]
    return {"answer": text, "found": True, "sources": [public(s) for s in cited], "related": related,
            "unknown_citations": unknown, "prompt_version": version}
