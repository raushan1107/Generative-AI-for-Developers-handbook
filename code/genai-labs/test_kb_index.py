"""Drill 06.5: the knowledge index, offline, with a fake embedding function.
Run:  pytest -q test_kb_index.py"""
import re
import zlib

import numpy as np
import pytest

import kb_index
from kb_index import KnowledgeIndex

CALLS = []


def fake_embed(texts):
    """Hashed bag of words: texts sharing words get similar vectors. Deterministic and free."""
    CALLS.append(len(texts))
    out = np.zeros((len(texts), 64), dtype=np.float32)
    for row, text in enumerate(texts):
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            out[row, zlib.crc32(word.encode()) % 64] += 1
        out[row, 0] += 0.01
    return out


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(kb_index, "embed", fake_embed)
    CALLS.clear()


def chunks():
    return [
        {"id": "refunds#1", "title": "Refunds > How much", "text": "refund 50 percent cancel early", "audience": "public"},
        {"id": "labs#1", "title": "Labs > Extensions", "text": "lab extension 49 dollars 14 days", "audience": "public"},
        {"id": "approvals#1", "title": "Approvals > Limits", "text": "refund exception approval team lead",
         "audience": "staff"},
    ]


def test_only_new_and_changed_chunks_are_embedded():
    first, stats = KnowledgeIndex.build(chunks())
    assert stats == {"new": 3, "changed": 0, "unchanged": 0, "removed": 0} and CALLS == [3]
    edited = chunks()[:2]
    edited[1] = edited[1] | {"text": "lab extension 59 dollars 14 days"}
    second, stats = KnowledgeIndex.build(edited, previous=first)
    assert stats == {"new": 0, "changed": 1, "unchanged": 1, "removed": 1} and CALLS == [3, 1]
    assert np.allclose(second.vectors[0], first.vectors[0])


def test_a_different_embedding_model_means_a_full_rebuild(monkeypatch):
    first, _ = KnowledgeIndex.build(chunks())
    monkeypatch.setattr(kb_index, "EMBED_MODEL", "another-model")
    _, stats = KnowledgeIndex.build(chunks(), previous=first)
    assert stats["new"] == 3


def test_audience_is_a_pre_filter():
    index, _ = KnowledgeIndex.build(chunks())
    public = index.search("refund exception approval", k=3)
    assert "approvals#1" not in [h["id"] for h in public]
    assert index.search("refund exception approval", k=1, audience=("public", "staff"))[0]["id"] == "approvals#1"


def test_relevance_floor_can_return_nothing():
    index, _ = KnowledgeIndex.build(chunks())
    assert index.search("lab extension", min_score=0.2)[0]["id"] == "labs#1"
    assert index.search("capital of france", min_score=0.5) == []


def test_save_load_and_model_check(tmp_path, monkeypatch):
    index, _ = KnowledgeIndex.build(chunks())
    index.save(tmp_path)
    again = KnowledgeIndex.load(tmp_path)
    assert again.manifest["chunks"] == 3 and again.chunks[0]["hash"] == index.chunks[0]["hash"]
    monkeypatch.setattr(kb_index, "EMBED_MODEL", "another-model")
    with pytest.raises(RuntimeError, match="rebuild"):
        KnowledgeIndex.load(tmp_path)


def test_a_new_chunker_version_means_a_full_rebuild(monkeypatch):
    first, _ = KnowledgeIndex.build(chunks())
    monkeypatch.setattr(kb_index, "CHUNKER_VERSION", "sections-v3")
    second, stats = KnowledgeIndex.build(chunks(), previous=first)
    assert stats["new"] == 3 and second.manifest["chunker"] == "sections-v3"
