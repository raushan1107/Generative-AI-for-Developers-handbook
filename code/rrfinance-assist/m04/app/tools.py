"""RR Finance Assist tools (milestone 4).
The model can ask for these; our code decides whether and how they run.
Identity rule: the signed-in customer comes from `context`, set by the app, never from the model."""
import json
import re
import time
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app import backend, policy
from app.config import TICKETS_FILE
from app.toolkit import Toolkit

kit = Toolkit()
ACCOUNT_ID = re.compile(r"AC-\d{4}")
CARD = re.compile(r"\d{4}")
TXN_ID = re.compile(r"TX-\d{4}")

# Friendly status lines the UI shows while a tool runs.
LABELS = {
    "search_products": "Searching the product catalogue",
    "get_product": "Looking up the product",
    "list_my_accounts": "Checking your accounts and cards",
    "list_my_transactions": "Looking at your recent payments",
    "get_card_status": "Checking your card",
    "quote_fee_refund": "Checking your overdraft fees under the policy",
    "quote_dispute": "Checking whether the payment can be disputed",
    "create_support_case": "Creating a case for the support team",
}


def _signed_in(context: dict) -> str:
    customer_id = context.get("customer_id")
    if customer_id not in backend.CUSTOMERS:
        raise PermissionError("no customer is signed in; ask them to sign in first")
    return customer_id


def _owned(table: dict, key: str, context: dict, what: str) -> dict:
    customer_id = _signed_in(context)
    record = table.get(key)
    if record is None or record["customer_id"] != customer_id:   # same answer for both: don't leak which IDs exist
        raise PermissionError(f"{key} is not one of the signed-in customer's {what}")
    return record


def _own_card(last4: str, context: dict) -> dict:
    return _owned(backend.CARDS, last4, context, "cards")


def _own_account(account_id: str, context: dict) -> dict:
    return _owned(backend.ACCOUNTS, account_id, context, "accounts")


def _own_transaction(txn_id: str, context: dict) -> dict:
    t = backend.TRANSACTIONS.get(txn_id)
    if t is None:
        _signed_in(context)
        raise PermissionError(f"{txn_id} is not a payment on the signed-in customer's cards")
    _owned(backend.CARDS, t["card"], context, "cards")
    return t


def _upper_match(pattern, example):
    def check(cls, v):
        v = v.strip().upper()
        if not pattern.fullmatch(v):
            raise ValueError(f"must look like {example}")
        return v
    return classmethod(check)


# ---------------------------------------------------------------- catalogue (no identity needed)
class SearchProductsArgs(BaseModel):
    family: Optional[Literal["accounts", "cards", "loans"]] = None
    audience: Optional[Literal["personal", "student", "business"]] = None
    max_annual_fee_usd: Optional[int] = Field(default=None, description="Highest annual fee in USD, or null")
    text: Optional[str] = Field(default=None, description="One keyword to match in names and descriptions")


@kit.register(SearchProductsArgs)
def search_products(args):
    """Search the RR Finance Bank product catalogue by family, audience, maximum annual fee and/or a keyword."""
    hits = [p for p in backend.PRODUCTS.values()
            if (not args.family or p["family"] == args.family)
            and (not args.audience or p["audience"] == args.audience)
            and (args.max_annual_fee_usd is None or p["annual_fee_usd"] <= args.max_annual_fee_usd)
            and (not args.text or args.text.lower() in (p["name"] + " " + p["description"]).lower())]
    return [{k: p[k] for k in ("id", "name", "family", "audience", "annual_fee_usd", "rate_pct", "rate_type")}
            for p in hits[:8]]


class ProductArgs(BaseModel):
    product_id: str = Field(description="Product ID like P110")


@kit.register(ProductArgs)
def get_product(args):
    """Full details of one product: description, fee, rate and who it is for."""
    return backend.PRODUCTS.get(args.product_id.strip().upper()) or {"error": f"no product {args.product_id}"}


# ---------------------------------------------------------------- the signed-in customer's data
class NoArgs(BaseModel):
    pass


@kit.register(NoArgs, needs_context=True)
def list_my_accounts(args, context):
    """List the signed-in customer's accounts (account_id, product, balance) and cards (card_last4, product, status)."""
    customer_id = _signed_in(context)
    return {"accounts": backend.accounts_of(customer_id), "cards": backend.cards_of(customer_id)}


class CardArg(BaseModel):
    card_last4: str = Field(description="Last four digits of one of the customer's cards, like 4821")
    _check = field_validator("card_last4")(_upper_match(CARD, "4821"))


@kit.register(CardArg, needs_context=True)
def list_my_transactions(args, context):
    """Payments on one of the signed-in customer's cards in the last 90 days: txn_id, date, merchant, amount."""
    _own_card(args.card_last4, context)
    since = (date.today() - timedelta(days=90)).isoformat()
    rows = [{"txn_id": tid, **t} for tid, t in backend.TRANSACTIONS.items()
            if t["card"] == args.card_last4 and t["date"] >= since]
    return sorted(rows, key=lambda r: r["date"], reverse=True)


@kit.register(CardArg, needs_context=True)
def get_card_status(args, context):
    """Status of one of the signed-in customer's cards: active, frozen or replacement sent (with its delivery date)."""
    card = _own_card(args.card_last4, context)
    return {"card_last4": args.card_last4, "product": backend.PRODUCTS[card["product_id"]]["name"],
            "status": card["status"], **({"replacement": card["replacement"]} if "replacement" in card else {})}


class AccountArg(BaseModel):
    account_id: str = Field(description="The customer's account ID, like AC-1234, from list_my_accounts")
    _check = field_validator("account_id")(_upper_match(ACCOUNT_ID, "AC-1234"))


@kit.register(AccountArg, needs_context=True)
def quote_fee_refund(args, context):
    """Overdraft fees on this account: which were charged in error and what RR Finance Bank would refund,
    under the fee policy. Always use this for fee refund amounts; never calculate them yourself."""
    a = _own_account(args.account_id, context)
    quote = policy.fee_refund_quote(backend.OVERDRAFT_DAYS.get(args.account_id, []), a["courtesy_refund_used"])
    return {"account_id": args.account_id, **quote}


class TransactionArg(BaseModel):
    txn_id: str = Field(description="Transaction ID like TX-1002, from list_my_transactions")
    _check = field_validator("txn_id")(_upper_match(TXN_ID, "TX-1234"))


@kit.register(TransactionArg, needs_context=True)
def quote_dispute(args, context):
    """Whether one of the customer's card payments can still be disputed today, and when a provisional credit would arrive."""
    t = _own_transaction(args.txn_id, context)
    return {"txn_id": args.txn_id, "merchant": t["merchant"], "amount_usd": t["amount_usd"],
            **policy.dispute_quote(date.fromisoformat(t["date"]), date.today())}


class CaseArgs(BaseModel):
    category: Literal["card", "dispute", "fraud", "fees", "transfers", "loans", "account", "other"]
    summary: str = Field(description="One or two sentences for the support team, in English")
    reference: Optional[str] = Field(default=None, description="Related account ID, card_last4 or txn_id, or null")
    urgency: Literal["low", "medium", "high"]

    @field_validator("summary")
    @classmethod
    def summary_length(cls, v):
        v = v.strip()
        if not 10 <= len(v) <= 400:
            raise ValueError("summary must be 10 to 400 characters")
        return v


@kit.register(CaseArgs, needs_context=True)
def create_support_case(args, context):
    """Create a case for the human support team. Use it for disputes and fraud you can't settle, fee exceptions,
    anything you can't resolve, or when the customer asks for a person. Tell the customer the case ID."""
    customer_id = _signed_in(context)
    ref = (args.reference or "").strip().upper()
    if ACCOUNT_ID.fullmatch(ref):
        _own_account(ref, context)
    elif CARD.fullmatch(ref):
        _own_card(ref, context)
    elif TXN_ID.fullmatch(ref):
        _own_transaction(ref, context)
    case = {"case_id": "CS-" + uuid.uuid4().hex[:6].upper(), "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "customer_id": customer_id, **args.model_dump()}
    path = Path(TICKETS_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:        # Module 07 adds human approval before actions like this
        f.write(json.dumps(case, ensure_ascii=False) + "\n")
    return {"case_id": case["case_id"], "status": "created", "team": args.category}


TOOLS = kit.schemas()
