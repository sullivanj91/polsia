from __future__ import annotations

from app.config import settings

_client = None

COLLECTIONS = ["company_memory", "competitor_profiles", "product_knowledge"]


def get_chroma_client():
    global _client
    if _client is None:
        import chromadb
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def get_collection(name: str):
    if name not in COLLECTIONS:
        raise ValueError(f"Unknown collection: {name}. Choose from {COLLECTIONS}")
    client = get_chroma_client()
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
