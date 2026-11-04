import unittest
from decimal import Decimal

from l5_release import (
    HEALTH_LIMITS,
    RateCard,
    cache_key,
    choose_demo_route,
    estimate_monthly_cost,
    health_failures,
    validate_manifest,
)


class ReleaseLabTests(unittest.TestCase):
    def test_cost_uses_supplied_rates(self):
        total = estimate_monthly_cost(
            1000, 200, 10_000, RateCard(Decimal("0.50"), Decimal("2.00"))
        )
        self.assertEqual(total, Decimal("9.00"))

    def test_cost_rejects_negative_counts(self):
        with self.assertRaises(ValueError):
            estimate_monthly_cost(
                -1, 200, 10_000, RateCard(Decimal("0.50"), Decimal("2.00"))
            )

    def test_cost_rejects_boolean_count(self):
        with self.assertRaises(TypeError):
            estimate_monthly_cost(
                True, 200, 10_000, RateCard(Decimal("0.50"), Decimal("2.00"))
            )

    def test_cache_key_includes_prompt_version(self):
        messages = [{"role": "user", "content": "Opening hours?"}]
        first = cache_key("model", "v1", messages)
        self.assertEqual(first, cache_key("model", "v1", messages))
        self.assertNotEqual(first, cache_key("model", "v2", messages))

    def test_demo_routing_is_explicit(self):
        self.assertEqual(choose_demo_route("simple", "public"), "small-model")
        self.assertEqual(choose_demo_route("complex", "public"), "large-model")
        self.assertEqual(
            choose_demo_route("simple", "customer"), "approved-private-route"
        )

    def test_manifest_and_health_checks(self):
        manifest = {
            "release_id": "demo",
            "model_deployment": "model",
            "prompt_version": "v1",
            "evaluation_dataset": "eval",
            "image_digest": "sha256:" + "a" * 64,
            "rollback_image_digest": "sha256:" + "b" * 64,
        }
        self.assertEqual(validate_manifest(manifest), [])
        self.assertEqual(
            health_failures(
                {
                    "p95_latency_ms": 1200.0,
                    "error_rate": 0.01,
                    "citation_id_failure_rate": 0.02,
                },
                HEALTH_LIMITS,
            ),
            [],
        )
        self.assertEqual(
            health_failures(
                {
                    "p95_latency_ms": 1600.0,
                    "error_rate": 0.01,
                    "citation_id_failure_rate": 0.02,
                },
                HEALTH_LIMITS,
            ),
            ["p95_latency_ms"],
        )


if __name__ == "__main__":
    unittest.main()
