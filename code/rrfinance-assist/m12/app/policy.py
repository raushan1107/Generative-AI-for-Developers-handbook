"""RR Finance Bank policy as code (fictional). Money and dates are decided here, never by the model."""
from datetime import date, timedelta

FEE_USD = 29                  # overdraft fee per overdrawn payment
FREE_BUFFER_USD = 50          # no fee if overdrawn by this much or less at the end of the day
MAX_FEES_PER_DAY = 3
DISPUTE_WINDOW_DAYS = 60      # stand-in rule: the payment date counts as the statement date


def fee_refund_quote(overdraft_days: list[dict], courtesy_used: bool) -> dict:
    """Which overdraft fees were charged in error (always refunded), plus one courtesy refund
    per 12 months if it hasn't been used. The Drill 03.7 case, decided by code."""
    charged = errors = 0
    lines = []
    for d in overdraft_days:
        allowed = 0 if -d["end_of_day_balance_usd"] <= FREE_BUFFER_USD else MAX_FEES_PER_DAY
        wrong = max(0, d["fees_charged"] - allowed)
        charged += d["fees_charged"]
        errors += wrong
        lines.append({"date": d["date"], "fees_charged": d["fees_charged"], "charged_in_error": wrong})
    courtesy = 1 if not courtesy_used and charged > errors else 0
    refund_fees = errors + courtesy
    return {"fees_charged": charged, "fees_charged_usd": charged * FEE_USD,
            "charged_in_error": errors, "courtesy_refund": bool(courtesy),
            "refund_usd": refund_fees * FEE_USD, "days": lines,
            "note": (f"{errors} fee(s) charged in error are refunded" if errors else "no fees were charged in error")
                    + ("; plus one courtesy refund" if courtesy else "")
                    + ("; the courtesy refund was already used this year" if courtesy_used else "")}


def dispute_quote(payment_date: date, today: date) -> dict:
    days = (today - payment_date).days
    if days > DISPUTE_WINDOW_DAYS:
        return {"allowed": False, "days_since_payment": days,
                "note": f"Disputes must be raised within {DISPUTE_WINDOW_DAYS} days; a case can ask the team to review it."}
    return {"allowed": True, "days_since_payment": days,
            "provisional_credit_by": (today + timedelta(days=14)).isoformat(),
            "note": "Inside the 60-day window: a provisional credit within 10 business days."}
