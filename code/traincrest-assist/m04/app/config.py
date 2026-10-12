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

# New in milestone 2
MAX_TURNS_KEPT = int(os.getenv("MAX_TURNS_KEPT", "6"))           # user/assistant pairs resent each turn
PRICE_IN_PER_M = float(os.getenv("PRICE_IN_PER_M", "0.40"))      # USD per 1M input tokens (check yours)
PRICE_OUT_PER_M = float(os.getenv("PRICE_OUT_PER_M", "1.60"))    # USD per 1M output tokens
LOG_FILE = os.getenv("LOG_FILE", "assist.log")

# New in milestone 4
MAX_TOOL_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "4"))          # tool calls allowed per turn, then stop
TICKETS_FILE = os.getenv("TICKETS_FILE", "data/tickets.jsonl")     # where create_support_ticket writes
# Some reasoning models reject tools on Chat Completions unless reasoning effort is "none".
_effort = os.getenv("TOOLS_REASONING_EFFORT", "").strip()
TOOL_EXTRAS = {"reasoning_effort": _effort} if _effort else {}
