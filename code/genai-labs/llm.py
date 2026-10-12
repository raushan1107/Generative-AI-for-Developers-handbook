"""Shared helper for every drill: returns an OpenAI-compatible client for
Azure OpenAI (Microsoft Foundry), OpenAI or Ollama, chosen in .env."""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # reads .env from the current folder

PROVIDER = os.getenv("LLM_PROVIDER", "azure").lower()


def get_client() -> OpenAI:
    if PROVIDER == "azure":
        # Azure OpenAI v1 API: the standard OpenAI client, pointed at your resource
        return OpenAI(
            base_url=os.environ["AZURE_OPENAI_BASE_URL"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
        )
    if PROVIDER == "openai":
        return OpenAI()  # reads OPENAI_API_KEY
    if PROVIDER == "ollama":
        return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER!r}")


# On Azure this is the DEPLOYMENT name; elsewhere it's the model name.
MODEL = {
    "azure": os.getenv("AZURE_OPENAI_DEPLOYMENT", "chat"),
    "openai": os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
    "ollama": os.getenv("OLLAMA_MODEL", "llama3.2"),
}.get(PROVIDER, "")
