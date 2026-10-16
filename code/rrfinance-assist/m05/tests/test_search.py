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


def test_documents_cover_products_and_help_sections():
    docs = load_documents()
    assert sum(d["kind"] == "product" for d in docs) == 20
    assert sum(d["kind"] == "help" for d in docs) == 44
    assert len({d["id"] for d in docs}) == len(docs)                  # ids are unique


def test_chunks_keep_article_and_section_titles():
    heading, text = next(chunk_by_headings("# Cards\nintro\n## Freeze it first\nFreeze it in the app."))
    assert heading == "Freeze it first" and text.startswith("Cards > Freeze it first\n")


def test_hybrid_search_finds_exact_terms(service):
    top = service.search("the 4 pm cut-off for wires", k=3, kind="help")[0]
    assert top["source"] == "transfers-and-payments.md" and "4 pm" in top["text"]


def test_filters_are_applied_before_ranking(service):
    hits = service.search("travel card with no foreign transaction fees", k=5, kind="product",
                          family="cards", max_annual_fee_usd=100)
    assert hits and all(h["family"] == "cards" and h["annual_fee_usd"] <= 100 for h in hits)
    assert hits[0]["id"] == "P111"
    assert service.search("anything", kind="product", max_annual_fee_usd=-1) == []


def test_index_save_and_load(service, tmp_path, monkeypatch):
    service.index.save(tmp_path)
    again = LocalIndex.load(tmp_path)
    assert len(again.docs) == len(service.index.docs)
    monkeypatch.setattr(search_module, "EMBED_MODEL", "another-model")
    with pytest.raises(RuntimeError, match="rebuild"):
        LocalIndex.load(tmp_path)


def test_search_tool_uses_the_index_and_falls_back(service, monkeypatch):
    def run(args):
        return json.loads(kit.dispatch("search_products", json.dumps(args)))

    none = {"family": None, "audience": None, "max_annual_fee_usd": None}
    monkeypatch.setattr(tools, "_search", service)
    assert run({"query": "Voyager Travel Card", **none})[0]["id"] == "P111"

    class Broken:
        def search(self, *a, **k):
            raise ConnectionError("embedding service down")

    monkeypatch.setattr(tools, "_search", Broken())                   # search down -> keyword fallback
    assert run({"query": "mortgage", **none})[0]["id"] == "P118"
    monkeypatch.setattr(tools, "_search", None)                       # no index -> keyword fallback
    assert run({"query": "students", **none, "family": "cards"})[0]["id"] == "P112"
