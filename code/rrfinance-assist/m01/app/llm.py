"""The only place in RR Finance Assist that knows how to reach the model."""
import os

from openai import OpenAI

from app.config import PROVIDER


def get_client() -> OpenAI:
    if PROVIDER == "azure":
        return OpenAI(base_url=os.environ["AZURE_OPENAI_BASE_URL"], api_key=os.environ["AZURE_OPENAI_API_KEY"])
    if PROVIDER == "openai":
        return OpenAI()
    if PROVIDER == "ollama":
        return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER!r}")
