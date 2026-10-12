"""Shared helper for the Claude 'Open alternative' boxes (native Anthropic SDK)."""
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()  # reads ANTHROPIC_API_KEY
CLAUDE_MODEL = "claude-opus-5-5"

# If a safety check declines a request, let the API retry it on another
# Claude model automatically. Pass these with client.beta.messages.create(...).
FALLBACK = dict(betas=["server-side-fallback-2026-07-01"], fallbacks="default")


def text_of(response) -> str:
    """Join the text blocks of a Claude response (it can also contain other block types)."""
    if response.stop_reason == "refusal":
        return "[The model declined this request.]"
    return "".join(b.text for b in response.content if b.type == "text")
