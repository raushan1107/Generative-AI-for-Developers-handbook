"""Structured logging and cost: one JSON line per event, ready for any log platform."""
import json
import logging
import time

from app.config import LOG_FILE, PRICE_IN_PER_M, PRICE_OUT_PER_M

_logger = logging.getLogger("traincrest_assist")
if not _logger.handlers:
    _handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


def log_event(**fields):
    """Write one JSON object per line. Never log API keys or full learner messages."""
    _logger.info(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **fields}, ensure_ascii=False))


def cost_usd(usage):
    """Dollar cost of one call from its token usage."""
    if usage is None:
        return None
    return (usage.prompt_tokens * PRICE_IN_PER_M + usage.completion_tokens * PRICE_OUT_PER_M) / 1_000_000
