"""Shared helper for every open-source lab: OpenAI-compatible clients for open models.

Option A (default): Ollama on your own computer. Free, private, no key. Ollama ignores the API key,
but the OpenAI library insists on one, so .env holds the placeholder "ollama".
Option B: a hosted provider of open models, with a free key, if your computer is too slow.
Change LLM_BASE_URL, LLM_API_KEY and CHAT_MODEL in .env; nothing else changes.
Embeddings always come from Ollama in these labs (EMBED_BASE_URL)."""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # reads .env from the current folder

BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("LLM_API_KEY", "ollama")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.2")
AGENT_MODEL = os.getenv("AGENT_MODEL") or CHAT_MODEL        # for tool calling and agents (Labs 2 and 3)
EMBED_BASE_URL = os.getenv("EMBED_BASE_URL", "http://localhost:11434/v1")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")


def get_client() -> OpenAI:
    return OpenAI(base_url=BASE_URL, api_key=API_KEY)


def get_embed_client() -> OpenAI:
    return OpenAI(base_url=EMBED_BASE_URL, api_key="ollama")
