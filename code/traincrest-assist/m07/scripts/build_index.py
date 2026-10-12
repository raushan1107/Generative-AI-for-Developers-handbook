"""Build the search index for Traincrest Assist (milestones 5 and 6).

From the project folder:  python -m scripts.build_index
SEARCH_BACKEND=local  -> embeds courses and help sections, saves data/index/ (vectors.npy + docs.json)
SEARCH_BACKEND=azure  -> creates or updates the Azure AI Search index and uploads the same documents
Re-run it whenever courses or help articles change, or when you switch embedding model or chunker."""
import time

from app.config import AZURE_SEARCH_API_KEY, AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX, EMBED_MODEL, SEARCH_BACKEND
from app.llm import get_client
from app.search import LocalIndex, embed, load_documents


def build_azure(client):
    from azure.core.credentials import AzureKeyCredential
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (HnswAlgorithmConfiguration, SearchableField, SearchField,
                                                       SearchFieldDataType, SearchIndex, SimpleField, VectorSearch,
                                                       VectorSearchProfile)
    docs = load_documents()
    vectors = embed(client, [d["text"] for d in docs])
    s = SearchFieldDataType
    fields = [
        SimpleField(name="id", type=s.String, key=True),
        SimpleField(name="kind", type=s.String, filterable=True),
        SearchableField(name="title", type=s.String),
        SearchableField(name="text", type=s.String, analyzer_name="en.microsoft"),   # stemming, stop words
        SimpleField(name="source", type=s.String),
        SimpleField(name="level", type=s.String, filterable=True),
        SimpleField(name="format", type=s.String, filterable=True),
        SimpleField(name="price_usd", type=s.Int32, filterable=True, sortable=True),
        SearchField(name="contentVector", type=s.Collection(s.Single), searchable=True,
                    vector_search_dimensions=vectors.shape[1], vector_search_profile_name="vprofile"),
    ]
    index = SearchIndex(name=AZURE_SEARCH_INDEX, fields=fields, vector_search=VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="vprofile", algorithm_configuration_name="hnsw")]))
    credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)
    SearchIndexClient(AZURE_SEARCH_ENDPOINT, credential).create_or_update_index(index)
    upload = [{**d, "contentVector": v.tolist()} for d, v in zip(docs, vectors)]
    results = SearchClient(AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_INDEX, credential).merge_or_upload_documents(upload)
    print(f"Azure AI Search index '{AZURE_SEARCH_INDEX}': {sum(r.succeeded for r in results)}/{len(upload)} documents.")


def main():
    client, start = get_client(), time.perf_counter()
    if SEARCH_BACKEND == "azure":
        build_azure(client)
    else:
        index = LocalIndex.build(client)
        index.save()
        kinds = [d["kind"] for d in index.docs]
        print(f"Local index: {kinds.count('course')} courses + {kinds.count('help')} help sections, "
              f"{index.vectors.shape[1]}-dimension vectors from {EMBED_MODEL}.")
    print(f"Done in {time.perf_counter() - start:.1f}s.")


if __name__ == "__main__":
    main()
