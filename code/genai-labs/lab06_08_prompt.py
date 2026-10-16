"""Drill 06.8: look at the exact prompt a RAG system sends. Then shrink the budget and watch
whole sources being dropped, lowest-ranked first."""
from kb_index import load_or_build
from rag_prompt import build_messages, count_tokens

question = "Can I get my overdraft fee refunded?"
hits = load_or_build().search(question, k=4)

messages, sources = build_messages(question, hits, max_context_tokens=1500)
for m in messages:
    print(f"----- {m['role']} ({count_tokens(m['content'])} tokens)\n{m['content']}\n")

for budget in (400, 150, 60):
    _, kept = build_messages(question, hits, max_context_tokens=budget)
    print(f"budget {budget:>4} tokens -> sources kept: {[h['id'] for h in kept]}")
