"""The only place in Traincrest Assist that knows how to reach the model."""
import os

from openai import OpenAI

from app.config import PROVIDER


def get_client() -> OpenAI:
    if PROVIDER == "azure":
        client = OpenAI(base_url=os.environ["AZURE_OPENAI_BASE_URL"], api_key=os.environ["AZURE_OPENAI_API_KEY"])
    elif PROVIDER == "openai":
        client = OpenAI()
    elif PROVIDER == "ollama":
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {PROVIDER!r}")
    # New in milestone 2: the SDK retries 408/409/429/5xx with backoff; give it 3 tries and a timeout.
    return client.with_options(max_retries=3, timeout=60)
