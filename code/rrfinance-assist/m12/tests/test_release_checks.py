from app.release_checks import health_failures, validate_release_manifest


def test_release_requires_versioned_artifacts_and_rollback_digest():
    manifest = {
        "release_id": "2026-10-17.1",
        "model_deployment": "chat",
        "prompt_version": "assist_system@v6",
        "evaluation_dataset": "eval-2026-10-17",
        "image_digest": "sha256:" + "a" * 64,
        "rollback_image_digest": "sha256:" + "b" * 64,
    }
    assert validate_release_manifest(manifest) == []


def test_release_rejects_missing_or_malformed_artifacts():
    failures = validate_release_manifest(
        {"release_id": "r1", "image_digest": "latest"}
    )
    assert failures == [
        "model_deployment",
        "prompt_version",
        "evaluation_dataset",
        "rollback_image_digest",
        "image_digest",
    ]


def test_health_thresholds_report_each_regression():
    observed = {
        "p95_latency_ms": 1200,
        "error_rate": 0.03,
        "citation_id_failure_rate": 0.01,
    }
    limits = {
        "p95_latency_ms": 1000,
        "error_rate": 0.02,
        "citation_id_failure_rate": 0.02,
    }
    assert health_failures(observed, limits) == ["p95_latency_ms", "error_rate"]


def test_missing_health_measurement_fails_closed():
    assert health_failures({}, {}) == [
        "p95_latency_ms",
        "error_rate",
        "citation_id_failure_rate",
    ]
