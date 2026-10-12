"""Drill 05.5 (and 05.9): the course catalogue in Azure AI Search.
Run:  python lab05_05_azure_search.py create
      python lab05_05_azure_search.py upload
      python lab05_05_azure_search.py query "make my app understand photos" --mode vector
      python lab05_05_azure_search.py query "AZ-104" --mode keyword
      python lab05_05_azure_search.py query "cloud admin certification" --mode hybrid --filter "price_usd le 1300"
Needs AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY and an embedding deployment (AZURE_OPENAI_EMBED_DEPLOYMENT)."""
import argparse
import os

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (HnswAlgorithmConfiguration, SearchableField, SearchField,
                                                   SearchFieldDataType, SearchIndex, SimpleField, VectorSearch,
                                                   VectorSearchProfile)
from azure.search.documents.models import VectorizedQuery

from catalogue import COURSES
from embed import embed

ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
INDEX = os.getenv("AZURE_SEARCH_INDEX", "courses")
credential = AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY", ""))


def build_index(dims: int) -> SearchIndex:
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="description", type=SearchFieldDataType.String),
        SimpleField(name="level", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="format", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="price_usd", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True, vector_search_dimensions=dims, vector_search_profile_name="vprofile"),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],             # approximate nearest neighbours
        profiles=[VectorSearchProfile(name="vprofile", algorithm_configuration_name="hnsw")])
    return SearchIndex(name=INDEX, fields=fields, vector_search=vector_search)


def create():
    dims = embed(["dimension check"]).shape[1]
    SearchIndexClient(ENDPOINT, credential).create_or_update_index(build_index(dims))
    print(f"Index '{INDEX}' ready ({dims}-dimension vectors).")


def upload():
    vectors = embed([f"{c['title']}. {c['description']}" for c in COURSES])
    docs = [{**{k: c[k] for k in ("id", "title", "description", "level", "format", "price_usd")},
             "contentVector": v.tolist()} for c, v in zip(COURSES, vectors)]
    results = SearchClient(ENDPOINT, INDEX, credential).merge_or_upload_documents(documents=docs)
    print(f"Uploaded {sum(r.succeeded for r in results)}/{len(docs)} courses.")


def query(text: str, mode: str, filter_: str | None, k: int = 3):
    search = SearchClient(ENDPOINT, INDEX, credential)
    vector_queries = None
    if mode in ("vector", "hybrid"):
        vector_queries = [VectorizedQuery(vector=embed([text])[0].tolist(), k_nearest_neighbors=k,
                                          fields="contentVector")]
    results = search.search(
        search_text=text if mode in ("keyword", "hybrid") else None,   # hybrid = both, merged with RRF
        vector_queries=vector_queries, filter=filter_, top=k,
        select=["id", "title", "level", "price_usd"])
    print(f"{mode} search: {text!r}" + (f"  filter: {filter_}" if filter_ else ""))
    for r in results:
        print(f"  {r['@search.score']:.4f}  {r['id']}  {r['title']}  ({r['level']}, ${r['price_usd']})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["create", "upload", "query"])
    ap.add_argument("text", nargs="?", default="")
    ap.add_argument("--mode", choices=["keyword", "vector", "hybrid"], default="hybrid")
    ap.add_argument("--filter", default=None, help="OData filter, e.g. \"level eq 'beginner' and price_usd le 500\"")
    a = ap.parse_args()
    {"create": create, "upload": upload}.get(a.action, lambda: query(a.text, a.mode, a.filter))()
