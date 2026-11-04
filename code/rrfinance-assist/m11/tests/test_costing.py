from decimal import Decimal

import pytest

from app.costing import RateCard, estimate_monthly_cost


def test_monthly_cost_uses_separate_input_and_output_rates():
    rates = RateCard(
        input_usd_per_million=Decimal("0.40"),
        output_usd_per_million=Decimal("1.60"),
    )
    assert estimate_monthly_cost(1000, 250, 40000, rates) == Decimal("32.000")


def test_zero_requests_cost_nothing():
    rates = RateCard(Decimal("1.00"), Decimal("2.00"))
    assert estimate_monthly_cost(1000, 500, 0, rates) == Decimal(0)


def test_negative_rate_is_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        RateCard(Decimal("-0.01"), Decimal("1.00"))


def test_negative_volume_is_rejected():
    rates = RateCard(Decimal("1.00"), Decimal("2.00"))
    with pytest.raises(ValueError, match="cannot be negative"):
        estimate_monthly_cost(1000, 500, -1, rates)
