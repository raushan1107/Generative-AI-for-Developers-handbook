"""Lab 5: illustrative routing, token-cost estimates and release preflight checks."""

import math
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RateCard:
    input_usd_per_million: Decimal
    output_usd_per_million: Decimal


def estimate_monthly_cost(
    input_tokens_per_request: int,
    output_tokens_per_request: int,
    requests_per_month: int,
    rate_card: RateCard,
) -> Decimal:
    counts = (
        input_tokens_per_request,
        output_tokens_per_request,
        requests_per_month,
    )
    if any(not isinstance(value, int) for value in counts):
        raise TypeError("Token counts and request volume must be integers")
    if any(value < 0 for value in counts):
        raise ValueError("Token counts and request volume must be non-negative")
    if any(isinstance(value, bool) for value in counts):
        raise TypeError("Token counts and request volume must be integers")
    rates = (rate_card.input_usd_per_million, rate_card.output_usd_per_million)
    if any(not isinstance(rate, Decimal) for rate in rates):
        raise TypeError("Rates must be Decimal values")
    if any(not rate.is_finite() or rate < 0 for rate in rates):
        raise ValueError("Rates must be finite and non-negative")

    input_cost = (
        Decimal(input_tokens_per_request * requests_per_month)
        * rate_card.input_usd_per_million
        / Decimal(1_000_000)
    )
    output_cost = (
        Decimal(output_tokens_per_request * requests_per_month)
        * rate_card.output_usd_per_million
        / Decimal(1_000_000)
    )
    return input_cost + output_cost


def cache_key(model: str, prompt_version: str, messages: list[dict[str, str]]) -> str:
    if not model or not prompt_version:
        raise ValueError("Model and prompt version are required")
    canonical = json.dumps(
        {"model": model, "prompt_version": prompt_version, "messages": messages},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def choose_demo_route(task: str, data_classification: str) -> str:
    if task not in {"simple", "complex"}:
        raise ValueError("Task must be 'simple' or 'complex'")
    if data_classification not in {"public", "customer"}:
        raise ValueError("Data classification must be 'public' or 'customer'")
    if data_classification == "customer":
        return "approved-private-route"
    return "small-model" if task == "simple" else "large-model"


REQUIRED_FIELDS = (
    "release_id",
    "model_deployment",
    "prompt_version",
    "evaluation_dataset",
    "image_digest",
    "rollback_image_digest",
)
IMAGE_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
HEALTH_LIMITS = {
    "p95_latency_ms": 1500.0,
    "error_rate": 0.02,
    "citation_id_failure_rate": 0.05,
}


def validate_manifest(manifest: Mapping[str, str]) -> list[str]:
    failures = [
        field for field in REQUIRED_FIELDS
        if not isinstance(manifest.get(field), str) or not manifest[field].strip()
    ]
    for field in ("image_digest", "rollback_image_digest"):
        value = manifest.get(field, "")
        if isinstance(value, str) and value and not IMAGE_DIGEST.fullmatch(value):
            failures.append(field)
    return failures


def health_failures(
    observed: Mapping[str, float], limits: Mapping[str, float]
) -> list[str]:
    failures: list[str] = []
    for name in HEALTH_LIMITS:
        value = observed.get(name)
        limit = limits.get(name)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or not isinstance(limit, (int, float))
            or isinstance(limit, bool)
            or not math.isfinite(limit)
            or value < 0
            or limit < 0
            or value > limit
        ):
            failures.append(name)
    return failures


def main() -> None:
    illustrative_rates = RateCard(Decimal("0.50"), Decimal("2.00"))
    monthly_cost = estimate_monthly_cost(1000, 200, 10_000, illustrative_rates)
    print(f"Illustrative monthly token estimate: ${monthly_cost:.2f}")
    key = cache_key(
        "example-model",
        "assist-v1",
        [{"role": "user", "content": "What are the bank's opening hours?"}],
    )
    print(f"Example cache key: {key[:12]}... (key only; no response cache is implemented)")

    for task, data_classification in (
        ("simple", "public"),
        ("complex", "public"),
        ("simple", "customer"),
    ):
        route = choose_demo_route(task, data_classification)
        print(f"Route {task}/{data_classification}: {route}")

    manifest = {
        "release_id": "demo-2026-01",
        "model_deployment": "example-model",
        "prompt_version": "assist-v1",
        "evaluation_dataset": "synthetic-eval-v1",
        "image_digest": "sha256:" + "a" * 64,
        "rollback_image_digest": "sha256:" + "b" * 64,
    }
    manifest_failures = validate_manifest(manifest)
    health = {
        "p95_latency_ms": 1200.0,
        "error_rate": 0.01,
        "citation_id_failure_rate": 0.02,
    }
    health_failures_found = health_failures(health, HEALTH_LIMITS)
    passed = not manifest_failures and not health_failures_found
    print(f"Local preflight: {'PASS' if passed else 'BLOCK'}")
    print("Placeholder digests prove only string shape, not artifact provenance.")
    print("Nothing was deployed or sent to a model provider.")


if __name__ == "__main__":
    main()
