"""Settings for Traincrest Assist, read from .env so nothing secret lives in code."""
import os

from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "azure").lower()

# On Azure this is the DEPLOYMENT name; elsewhere it's the model name.
MODEL = {
    "azure": os.getenv("AZURE_OPENAI_DEPLOYMENT", "chat"),
    "openai": os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
    "ollama": os.getenv("OLLAMA_MODEL", "llama3.2"),
}.get(PROVIDER, "")

# New in milestone 2
MAX_TURNS_KEPT = int(os.getenv("MAX_TURNS_KEPT", "6"))           # user/assistant pairs resent each turn
PRICE_IN_PER_M = float(os.getenv("PRICE_IN_PER_M", "0.40"))      # USD per 1M input tokens (check yours)
PRICE_OUT_PER_M = float(os.getenv("PRICE_OUT_PER_M", "1.60"))    # USD per 1M output tokens
LOG_FILE = os.getenv("LOG_FILE", "assist.log")
