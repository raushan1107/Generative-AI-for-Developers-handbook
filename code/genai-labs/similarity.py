"""Drill 05.2: the three ways to compare vectors, written out by hand."""
import numpy as np


def dot(a, b) -> float:
    return float(np.dot(a, b))


def cosine(a, b) -> float:
    """Angle-based: 1.0 = same direction, 0 = unrelated, -1 = opposite. Ignores length."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def euclidean(a, b) -> float:
    """Straight-line distance: 0 = identical. Smaller is more similar."""
    return float(np.linalg.norm(np.asarray(a) - np.asarray(b)))


def cosine_matrix(vectors) -> np.ndarray:
    """Every pair at once: normalise rows to length 1, then one matrix multiply."""
    v = np.asarray(vectors, dtype=np.float32)
    v = v / np.linalg.norm(v, axis=1, keepdims=True)
    return v @ v.T
