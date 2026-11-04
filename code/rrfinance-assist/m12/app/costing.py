"""Cost estimates from an explicitly supplied, current rate card."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RateCard:
    input_usd_per_million: Decimal
    output_usd_per_million: Decimal

    def __post_init__(self) -> None:
        rates = (self.input_usd_per_million, self.output_usd_per_million)
        if any(not isinstance(rate, Decimal) for rate in rates):
            raise TypeError("Token rates must use Decimal values")
        if any(not rate.is_finite() or rate < 0 for rate in rates):
            raise ValueError("Token rates cannot be negative")


def estimate_monthly_cost(
    input_tokens_per_request: int,
    output_tokens_per_request: int,
    requests_per_month: int,
    rate_card: RateCard,
) -> Decimal:
    values = (
        input_tokens_per_request,
        output_tokens_per_request,
        requests_per_month,
    )
    if any(value < 0 for value in values):
        raise ValueError("Token counts and request volume cannot be negative")

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
