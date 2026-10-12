"""Settings for Traincrest Assist, read from .env so nothing secret lives in code."""
import os

from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()   # default: a free local model (Ollama)

# On Azure this is the DEPLOYMENT name; elsewhere it's the model name.
MODEL = {
    "azure": os.getenv("AZURE_OPENAI_DEPLOYMENT", "chat"),
    "openai": os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
    "ollama": os.getenv("OLLAMA_MODEL", "llama3.2"),
}.get(PROVIDER, "")
