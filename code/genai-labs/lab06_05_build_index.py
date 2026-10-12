"""Drill 06.5: build or update the knowledge index (help centre + internal documents).
Run it twice: the second run embeds nothing. Edit one document and run it again: only that
document's changed chunks are embedded."""
import time

from ingest import load_knowledge_base
from kb_index import INDEX_DIR, KnowledgeIndex
from rag_chunks import chunk_all

start = time.perf_counter()
try:
    previous = KnowledgeIndex.load(check_model=False)       # build() decides whether its vectors can be reused
except FileNotFoundError:
    previous = None
chunks = chunk_all(load_knowledge_base())
index, stats = KnowledgeIndex.build(chunks, previous)
index.save()

print(f"chunks: {len(chunks)}  ->  new {stats['new']}, changed {stats['changed']}, "
      f"unchanged {stats['unchanged']}, removed {stats['removed']}")
print(f"embedded this run: {stats['new'] + stats['changed']}  ·  {time.perf_counter() - start:.1f}s")
print(f"saved to {INDEX_DIR.name}/: vectors.npy {index.vectors.shape}, chunks.json, manifest.json")
print("manifest:", index.manifest)
