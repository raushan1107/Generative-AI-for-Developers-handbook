"""Module 07: the agent's tools over desk.py. Read tools look things up; write tools change state.
The signed-in customer comes from `context`, set by the app, never from the model.
WRITE_TOOLS lists the tools that need a human's approval; preview() says, in plain words,
exactly what an approval would do, so the human approves an effect, not a function name."""
import functools
import json
from typing import Literal

from pydantic import BaseModel, Field

import desk
from toolkit import Toolkit

kit = Toolkit()
WRITE_TOOLS = {"freeze_card", "open_dispute"}


def actionable(func):
    """Errors are observations: return the system's message so the model can recover
    (pick another payment, offer a case, retry), instead of a generic "tool failed"."""
    @functools.wraps(func)
    def wrapper(args, context):
        try:
            return func(args, context)
        except desk.DeskError as e:
            return {"error": str(e)}
        except TimeoutError as e:
            return {"error": str(e), "retryable": True}
    return wrapper


class NoArgs(BaseModel):
    pass


class CardArgs(BaseModel):
    card_last4: str = Field(description="Last four digits of one of the customer's cards, like 4821, from my_cards")


class TransactionArgs(BaseModel):
    txn_id: str = Field(description="Transaction ID like TX-1002, from recent_transactions")


class DisputeArgs(BaseModel):
    txn_id: str = Field(description="Transaction ID like TX-1002, from recent_transactions")
    reason: Literal["charged_twice", "wrong_amount", "not_received", "not_recognised"]


class CaseArgs(BaseModel):
    category: Literal["card", "dispute", "fraud", "fees", "other"]
    summary: str = Field(description="One or two sentences for the support team")


@kit.register(NoArgs, needs_context=True)
@actionable
def my_cards(args, context):
    """List the signed-in customer's cards: card_last4, product and status (active or frozen)."""
    return desk.my_cards(context["customer"])


@kit.register(CardArgs, needs_context=True)
@actionable
def card_status(args, context):
    """Status of one card: active or frozen, and what that means for payments."""
    return desk.card_status(context["customer"], args.card_last4)


@kit.register(CardArgs, needs_context=True)
@actionable
def recent_transactions(args, context):
    """Payments on one card in the last 90 days: txn_id, date, merchant and amount, newest first."""
    return desk.recent_transactions(context["customer"], args.card_last4)


@kit.register(TransactionArgs, needs_context=True)
@actionable
def dispute_quote(args, context):
    """Whether a payment can be disputed today, and when a provisional credit would arrive. Call it before open_dispute."""
    return desk.dispute_quote(context["customer"], args.txn_id)


@kit.register(CardArgs, needs_context=True)
@actionable
def freeze_card(args, context):
    """Freeze one card so new payments are declined. Changes the account: needs the customer's approval."""
    return desk.freeze_card(context["customer"], args.card_last4, key=context.get("idempotency_key"))


@kit.register(DisputeArgs, needs_context=True)
@actionable
def open_dispute(args, context):
    """Open a dispute for one payment and start the provisional credit. Changes the account: needs the
    customer's approval. Call dispute_quote first."""
    return desk.open_dispute(context["customer"], args.txn_id, args.reason, key=context.get("idempotency_key"))


@kit.register(CaseArgs, needs_context=True)
@actionable
def create_case(args, context):
    """Create a case for the human support team, for anything you can't do yourself."""
    return desk.create_case(context["customer"], args.category, args.summary)


def preview(name: str, arguments: str, context: dict) -> str:
    """What an approval would do, in the customer's terms, computed by code (not described by the model)."""
    a = json.loads(arguments or "{}")
    customer = context["customer"]
    try:
        if name == "freeze_card":
            card = desk.card_status(customer, a["card_last4"])
            return (f"Freeze your {card['product']} ending {a['card_last4']}: new payments and cash withdrawals "
                    "will be declined until you unfreeze it; direct debits keep working.")
        if name == "open_dispute":
            quote = desk.dispute_quote(customer, a["txn_id"])
            txn = desk.STATE["transactions"][a["txn_id"].upper()]
            if not quote["allowed"]:
                return f"Dispute {a['txn_id']} (not possible: {quote['reason']})."
            return (f"Dispute ${txn['amount_usd']:.2f} to {txn['merchant']} on {txn['date']} ({a.get('reason')}); "
                    f"a provisional credit by {quote['provisional_credit_by']}.")
    except (desk.DeskError, KeyError) as e:
        return f"{name} with {arguments} (can't preview: {e})"
    return f"{name} with {arguments}"


SYSTEM = f"""You are RR Finance Assist, acting for the signed-in RR Finance Bank customer. Today is {desk.TODAY.isoformat()}.
- Use tools to look things up and to act. Never guess or invent card numbers, transaction IDs, dates or amounts.
- The customer can't see or call tools. Never ask them to; call the tools yourself.
- Never ask for a full card number, a PIN, a password or a one-time code.
- Start with my_cards whenever you need a card; use recent_transactions to find a payment's txn_id.
- Before open_dispute, call dispute_quote.
- freeze_card and open_dispute need the customer's approval; the system asks them. If they decline, don't try again.
- If a tool returns an error, use its message: correct the call, choose another option, or offer create_case.
- Finish with a short answer (at most 80 words) stating what was done, with dates and amounts."""
