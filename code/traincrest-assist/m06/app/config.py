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

# New in milestone 5: embeddings and search
EMBED_MODEL = {
    "azure": os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "embed"),
    "openai": os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
    "ollama": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
}.get(PROVIDER, "")
SEARCH_BACKEND = os.getenv("SEARCH_BACKEND", "local").lower()      # local (numpy file) | azure (Azure AI Search)
INDEX_DIR = os.getenv("INDEX_DIR", "data/index")                    # where the local index is saved
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "traincrest")

# New in milestone 6: answers grounded in the help centre (RAG)
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))                         # help sections retrieved per search
# Relevance floor on cosine similarity. Model-specific: calibrate it for yours with Drill 06.6.
_FLOORS = {"nomic-embed-text": 0.55, "text-embedding-3-small": 0.30, "text-embedding-3-large": 0.30}
RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE") or _FLOORS.get(EMBED_MODEL, 0.30))
RAG_MAX_CONTEXT_TOKENS = int(os.getenv("RAG_MAX_CONTEXT_TOKENS", "1500"))   # budget for sources in one prompt
HELP_CENTRE_URL = os.getenv("HELP_CENTRE_URL", "https://help.traincrest.example/")
