"""Drill 05.4: the spec for vector_store.py. Offline: hand-made 3-D vectors, no model.
Run:  pytest -q test_vector_store.py"""
import pytest

from vector_store import VectorStore, matches


@pytest.fixture
def store():
    s = VectorStore()
    s.add(ids=["refunds", "labs", "vouchers"],
          vectors=[[1, 0, 0], [0, 1, 0], [0.7, 0, 0.7]],
          texts=["Refund rules", "Lab extensions", "Exam vouchers"],
          metadatas=[{"topic": "billing", "words": 180}, {"topic": "labs", "words": 120},
                     {"topic": "exams", "words": 90}])
    return s


def test_nearest_first(store):
    hits = store.search([0.9, 0.1, 0.1], k=2)
    assert [h["id"] for h in hits] == ["refunds", "vouchers"]
    assert hits[0]["score"] > hits[1]["score"]


def test_length_does_not_matter(store):
    assert store.search([10, 0, 0], k=1)[0]["score"] == pytest.approx(1.0)


def test_filter_before_ranking(store):
    hits = store.search([1, 0, 0], k=3, where={"words": {"$lte": 120}})
    assert [h["id"] for h in hits] == ["vouchers", "labs"]


def test_matches_operators():
    meta = {"level": "beginner", "price_usd": 290}
    assert matches(meta, {"level": "beginner", "price_usd": {"$lte": 300}})
    assert not matches(meta, {"level": {"$in": ["advanced", "intermediate"]}})
    assert not matches(meta, {"format": "classroom"})          # missing field never matches


def test_save_and_load(store, tmp_path):
    store.save(tmp_path / "idx")
    again = VectorStore.load(tmp_path / "idx")
    assert again.search([0, 1, 0], k=1)[0]["text"] == "Lab extensions"
