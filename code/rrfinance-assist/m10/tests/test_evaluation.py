import pytest

from app.evaluation import classification_metrics, release_gate


def test_classification_metrics_highlight_fraud_recall():
    actual = ["fraud", "fraud", "fees", "dispute"]
    predicted = ["fraud", "fees", "fraud", "dispute"]
    metrics = classification_metrics(actual, predicted, positive_label="fraud")
    assert metrics == {"accuracy": 0.5, "precision": 0.5, "recall": 0.5}


def test_release_gate_checks_each_declared_threshold():
    metrics = {"accuracy": 0.94, "fraud_recall": 0.82}
    assert release_gate(metrics, {"accuracy": 0.9, "fraud_recall": 0.8}) == []
    assert release_gate(metrics, {"accuracy": 0.9, "fraud_recall": 0.9}) == [
        "fraud_recall"
    ]


@pytest.mark.parametrize(
    ("expected", "predicted"),
    [([], []), (["fraud"], [])],
)
def test_metric_inputs_must_be_nonempty_and_aligned(expected, predicted):
    with pytest.raises(ValueError, match="non-empty and aligned"):
        classification_metrics(expected, predicted, positive_label="fraud")


def test_release_gate_fails_missing_and_nonfinite_metrics():
    assert release_gate({"accuracy": float("nan")}, {"accuracy": 0.9, "recall": 0.8}) == [
        "accuracy",
        "recall",
    ]
