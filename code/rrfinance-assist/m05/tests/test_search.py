"""Milestone 5: documents, the local hybrid index, filters and the upgraded search tool.
Offline with a fake embedding model. Run:  pytest -q"""
import json

import pytest

from app import search as search_module
from app import tools
from app.search import LocalIndex, SearchService, chunk_by_headings, load_documents
from app.tools import kit
from tests.fakes import FakeClient


@pytest.fixture(scope="module")
def service():
    client = FakeClient()
    return SearchService(client, index=LocalIndex.build(client))


def test_documents_cover_courses_and_help_sections():
    docs = load_documents()
    assert sum(d["kind"] == "course" for d in docs) == 20
    assert sum(d["kind"] == "help" for d in docs) == 40
    assert len({d["id"] for d in docs}) == len(docs)                  # ids are unique


def test_chunks_keep_article_and_section_titles():
    heading, text = next(chunk_by_headings("# Labs\nintro\n## Problems\nLAB-503 means wait."))
    assert heading == "Problems" and text.startswith("Labs > Problems\n")


def test_hybrid_search_finds_exact_codes(service):
    top = service.search("I get error LAB-503", k=3, kind="help")[0]
    assert top["source"] == "labs-and-sandboxes.md" and "LAB-503" in top["text"]


def test_filters_are_applied_before_ranking(service):
    hits = service.search("python programming course", k=5, kind="course", level="beginner", max_price_usd=300)
    assert hits and all(h["level"] == "beginner" and h["price_usd"] <= 300 for h in hits)
    assert hits[0]["id"] == "C101"
    assert service.search("anything", kind="course", max_price_usd=10) == []


def test_index_save_and_load(service, tmp_path, monkeypatch):
    service.index.save(tmp_path)
    again = LocalIndex.load(tmp_path)
    assert len(again.docs) == len(service.index.docs)
    monkeypatch.setattr(search_module, "EMBED_MODEL", "another-model")
    with pytest.raises(RuntimeError, match="rebuild"):
        LocalIndex.load(tmp_path)


def test_search_tool_uses_the_index_and_falls_back(service, monkeypatch):
    def run(args):
        return json.loads(kit.dispatch("search_courses", json.dumps(args)))

    monkeypatch.setattr(tools, "_search", service)
    assert run({"query": "AZ-104 Azure Administrator", "level": None, "max_price_usd": None, "format": None})[0]["id"] == "C110"

    class Broken:
        def search(self, *a, **k):
            raise ConnectionError("embedding service down")

    monkeypatch.setattr(tools, "_search", Broken())                   # search down -> keyword fallback
    assert run({"query": "kubernetes", "level": None, "max_price_usd": None, "format": None})[0]["id"] == "C113"
    monkeypatch.setattr(tools, "_search", None)                       # no index -> keyword fallback
    assert run({"query": "docker", "level": "beginner", "max_price_usd": None, "format": None})[0]["id"] == "C114"
