import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chroma_client import get_collection
from app.models.memory import MemoryEntry

VALID_CATEGORIES = {"competitor", "strategy", "market", "customer_feedback", "learning", "product"}
CATEGORY_TO_COLLECTION = {
    "competitor": "competitor_profiles",
    "strategy": "company_memory",
    "market": "company_memory",
    "customer_feedback": "product_knowledge",
    "learning": "company_memory",
    "product": "product_knowledge",
}


async def store_memory(
    db: AsyncSession,
    category: str,
    title: str,
    content: str,
    source: str | None = None,
    tags: list[str] | None = None,
) -> MemoryEntry:
    chroma_id = str(uuid.uuid4())
    collection_name = CATEGORY_TO_COLLECTION.get(category, "company_memory")

    # Write to ChromaDB
    collection = get_collection(collection_name)
    collection.add(
        documents=[content],
        metadatas=[{"category": category, "title": title, "source": source or ""}],
        ids=[chroma_id],
    )

    # Write to PostgreSQL
    entry = MemoryEntry(
        category=category,
        title=title,
        content=content,
        source=source,
        tags=tags or [],
        chroma_id=chroma_id,
    )
    db.add(entry)
    await db.flush()
    return entry


async def search_memory(
    db: AsyncSession,
    query: str,
    category: str | None = None,
    n_results: int = 5,
) -> list[dict[str, Any]]:
    collections_to_search = []
    if category:
        coll = CATEGORY_TO_COLLECTION.get(category, "company_memory")
        collections_to_search = [coll]
    else:
        collections_to_search = ["company_memory", "competitor_profiles", "product_knowledge"]

    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for coll_name in collections_to_search:
        collection = get_collection(coll_name)
        try:
            qr = collection.query(query_texts=[query], n_results=min(n_results, 10))
            for i, doc in enumerate(qr["documents"][0]):
                chroma_id = qr["ids"][0][i]
                if chroma_id in seen_ids:
                    continue
                seen_ids.add(chroma_id)
                meta = qr["metadatas"][0][i] if qr["metadatas"] else {}
                results.append(
                    {
                        "chroma_id": chroma_id,
                        "content": doc,
                        "category": meta.get("category", ""),
                        "title": meta.get("title", ""),
                        "source": meta.get("source", ""),
                        "distance": qr["distances"][0][i] if qr.get("distances") else None,
                    }
                )
        except Exception:
            continue

    results.sort(key=lambda x: x.get("distance") or 0)
    return results[:n_results]


async def list_memories(
    db: AsyncSession, category: str | None = None, limit: int = 50
) -> list[MemoryEntry]:
    q = select(MemoryEntry).order_by(MemoryEntry.created_at.desc()).limit(limit)
    if category:
        q = q.where(MemoryEntry.category == category)
    result = await db.execute(q)
    return list(result.scalars().all())
