"""Local release and health checks; these do not deploy or monitor Azure resources."""

import math
import re
from collections.abc import Mapping


_REQUIRED_ARTIFACTS = (
    "release_id",
    "model_deployment",
    "prompt_version",
    "evaluation_dataset",
    "image_digest",
    "rollback_image_digest",
)
_IMAGE_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_HEALTH_METRICS = ("p95_latency_ms", "error_rate", "citation_id_failure_rate")


def validate_release_manifest(manifest: Mapping[str, str]) -> list[str]:
    failures = [
        name
        for name in _REQUIRED_ARTIFACTS
        if not isinstance(manifest.get(name), str) or not manifest[name].strip()
    ]
    for name in ("image_digest", "rollback_image_digest"):
        value = manifest.get(name, "")
        if isinstance(value, str) and value and not _IMAGE_DIGEST.fullmatch(value):
            failures.append(name)
    return failures


def health_failures(
    observed: Mapping[str, float], limits: Mapping[str, float]
) -> list[str]:
    failures: list[str] = []
    for name in _HEALTH_METRICS:
        value = observed.get(name)
        limit = limits.get(name)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not isinstance(limit, (int, float))
            or isinstance(limit, bool)
            or not math.isfinite(value)
            or not math.isfinite(limit)
            or value < 0
            or limit < 0
            or value > limit
        ):
            failures.append(name)
    return failures
