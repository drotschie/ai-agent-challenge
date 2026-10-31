"""ChromaDB vector store backed by FastEmbed local embeddings."""

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

import chromadb
from fastembed import TextEmbedding

from app.config import get_settings
from app.rag.chunkers import load_and_chunk_all_sources
from app.rag.schemas import DocumentChunk, RetrievedChunk

# Disable symlinks warning on Windows for clean logs
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


@lru_cache(maxsize=1)
def get_embedder() -> TextEmbedding:
    """Return cached FastEmbed embedding model instance.

    Loads BAAI/bge-small-en-v1.5 from local disk cache once per process.
    """
    settings = get_settings()
    return TextEmbedding(
        model_name="BAAI/bge-small-en-v1.5",
        cache_dir=str(settings.fastembed_cache_path),
    )


class GardenVectorStore:
    """Vector store for Cape gardener guide chunks with cosine similarity."""

    def __init__(
        self,
        persist_dir: Path | None = None,
        ephemeral: bool = False,
        collection_name: str = "sa_gardener_guide",
    ) -> None:
        """Initialize ChromaDB vector store in persistent or ephemeral mode."""
        self.collection_name = collection_name
        self.ephemeral = ephemeral

        if ephemeral:
            self.client = chromadb.EphemeralClient()
        else:
            target_dir = persist_dir if persist_dir is not None else get_settings().chroma_db_dir
            target_dir = Path(target_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(target_dir))

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        """Return total number of chunks currently indexed in the collection."""
        return self.collection.count()

    def index_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Embed and upsert document chunks into the collection.

        Returns the number of chunks indexed.
        """
        if not chunks:
            return 0

        embedder = get_embedder()
        texts = [c.text for c in chunks]
        embeddings_raw = list(embedder.embed(texts))
        embeddings = [
            e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings_raw
        ]

        self.collection.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[c.metadata for c in chunks],
        )
        return len(chunks)

    def ensure_indexed(self, data_dir: Path | None = None) -> int:
        """Index all reference chunks if the collection is empty.

        Returns total count of indexed chunks.
        """
        if self.count() == 0:
            chunks = load_and_chunk_all_sources(data_dir=data_dir)
            self.index_chunks(chunks)
        return self.count()

    def search(
        self,
        query: str,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
        min_similarity: float = 0.20,
    ) -> list[RetrievedChunk]:
        """Search chunks by cosine similarity with optional metadata filter.

        Converts cosine distance into similarity (1.0 - distance), filters by min_similarity,
        and returns results sorted descending by score.
        """
        total_items = self.count()
        if total_items == 0 or top_k <= 0:
            return []

        embedder = get_embedder()
        query_embeddings = [
            e.tolist() if hasattr(e, "tolist") else list(e)
            for e in embedder.embed([query])
        ]

        query_kwargs: dict[str, Any] = {
            "query_embeddings": query_embeddings,
            "n_results": min(top_k, total_items),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        results = self.collection.query(**query_kwargs)
        retrieved: list[RetrievedChunk] = []

        if results and results.get("ids") and results["ids"]:
            ids = results["ids"][0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for chunk_id, doc, meta, dist in zip(ids, documents, metadatas, distances):
                similarity = max(0.0, round(1.0 - float(dist), 4))
                if similarity >= min_similarity:
                    chunk_meta = dict(meta) if meta else {}
                    retrieved.append(
                        RetrievedChunk(
                            chunk_id=chunk_id,
                            source_file=str(chunk_meta.get("source_file", "")),
                            locator=str(chunk_meta.get("locator", "")),
                            similarity=similarity,
                            text=str(doc),
                            metadata=chunk_meta,
                        )
                    )

        retrieved.sort(key=lambda x: x.similarity, reverse=True)
        return retrieved


@lru_cache(maxsize=1)
def get_vector_store() -> GardenVectorStore:
    """Return cached persistent GardenVectorStore singleton, ensuring it is indexed."""
    store = GardenVectorStore()
    store.ensure_indexed()
    return store
