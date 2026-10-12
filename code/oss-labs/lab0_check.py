"""Lab 0: check your open-source lab environment. One line per check; fix any FAIL before Lab 1.
Run:  python lab0_check.py"""
import json
import sys
import time
import urllib.request

from client import BASE_URL, CHAT_MODEL, EMBED_BASE_URL, EMBED_MODEL, get_client, get_embed_client

OLLAMA = EMBED_BASE_URL.removesuffix("/v1")
failures = 0


def check(name, fn):
    global failures
    try:
        print(f"[ OK ] {name}: {fn()}")
    except Exception as e:
        failures += 1
        print(f"[FAIL] {name}: {type(e).__name__}: {e}")


def python_version():
    if sys.version_info < (3, 10):
        raise RuntimeError(f"Python {sys.version.split()[0]} is too old; install 3.10 or later")
    return sys.version.split()[0]


def ollama_running():
    with urllib.request.urlopen(f"{OLLAMA}/api/version", timeout=5) as r:
        return "Ollama " + json.load(r)["version"]


def models_pulled():
    with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=5) as r:
        names = {m["name"] for m in json.load(r)["models"]}
    wanted = [EMBED_MODEL] + ([CHAT_MODEL] if "localhost" in BASE_URL else [])
    missing = [m for m in wanted if m not in names and f"{m}:latest" not in names]
    if missing:
        raise RuntimeError("not pulled yet: " + ", ".join(missing) + "  ->  run: ollama pull <name>")
    return ", ".join(sorted(names))


def chat_works():
    start = time.perf_counter()
    r = get_client().chat.completions.create(
        model=CHAT_MODEL, messages=[{"role": "user", "content": "Reply with exactly one word: ready"}])
    return f"{CHAT_MODEL} says {r.choices[0].message.content.strip()!r} in {time.perf_counter() - start:.1f}s"


def embeddings_work():
    r = get_embed_client().embeddings.create(model=EMBED_MODEL, input=["hello world"])
    return f"{EMBED_MODEL} returns {len(r.data[0].embedding)} numbers per text"


check("Python", python_version)
check("Ollama server", ollama_running)
check("Models", models_pulled)
check("Chat model", chat_works)
check("Embedding model", embeddings_work)
print("\nAll checks passed. You're ready for Lab 1." if not failures else f"\n{failures} check(s) failed. "
      "See Troubleshooting in Lab 0.")
