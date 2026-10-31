"""Build and verify the persistent ChromaDB vector store index for Part 1 RAG."""

from pathlib import Path
import sys

# Ensure backend root is on sys.path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.rag.chunkers import load_and_chunk_all_sources
from app.rag.vector_store import GardenVectorStore


def main() -> None:
    """Load reference data, index chunks into ChromaDB, and verify with a test search."""
    settings = get_settings()
    data_dir = settings.data_dir
    print(f"Loading and chunking data sources from {data_dir}...")
    chunks = load_and_chunk_all_sources(data_dir=data_dir)
    print(f"Generated {len(chunks)} document chunks.")

    store = GardenVectorStore()
    indexed_count = store.index_chunks(chunks)
    total_count = store.count()
    print(f"Indexed {indexed_count} chunks. Total in collection: {total_count}.")

    if total_count != 125:
        raise ValueError(f"Expected 125 chunks, found {total_count}")

    test_query = "Woodstock sandy_loam lime dosage"
    print(f"Executing test search for: '{test_query}'...")
    results = store.search(query=test_query, top_k=5)
    print(f"Search returned {len(results)} results:")
    for idx, r in enumerate(results, start=1):
        preview = r.text[:120].replace("\n", " ")
        print(f"  [{idx}] ({r.similarity:.4f}) [{r.source_file} | {r.locator}] {preview}...")


if __name__ == "__main__":
    main()
