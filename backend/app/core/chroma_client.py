import chromadb
from chromadb import Collection

from app.config import settings

_client: chromadb.PersistentClient | None = None

COLLECTIONS = ["company_memory", "competitor_profiles", "product_knowledge"]


def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client


def get_collection(name: str) -> Collection:
    if name not in COLLECTIONS:
        raise ValueError(f"Unknown collection: {name}. Choose from {COLLECTIONS}")
    client = get_chroma_client()
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
