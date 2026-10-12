"""TrainCrest policy as code (fictional). Money and dates are decided here, never by the model."""
from datetime import date


def refund_quote(start_date: date, today: date, paid_usd: float) -> dict:
    days = (start_date - today).days
    if days < 0:
        return {"days_before_start": days, "refund_percent": 0, "refund_usd": 0.0,
                "note": "The course has already started, so it can't be cancelled for a refund."}
    if days >= 14:
        percent, note = 100, "Full refund: 14 or more days before the start."
    elif days >= 7:
        percent, note = 50, "50% refund: 7 to 13 days before the start."
    else:
        percent, note = 0, "No refund under 7 days, but the learner can move to a later date once, free."
    return {"days_before_start": days, "refund_percent": percent,
            "refund_usd": round(paid_usd * percent / 100, 2), "note": note}


def reschedule_fee(start_date: date, today: date) -> dict:
    days = (start_date - today).days
    if days < 0:
        return {"allowed": False, "fee_usd": None, "note": "The course has started; rescheduling isn't possible."}
    if days >= 7:
        return {"allowed": True, "fee_usd": 0, "note": "Free: 7 or more days before the start."}
    return {"allowed": True, "fee_usd": 50, "note": "Within 7 days: one reschedule for $50."}
