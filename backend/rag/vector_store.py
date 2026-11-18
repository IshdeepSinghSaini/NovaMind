"""
vector_store.py - Everything that talks to ChromaDB lives here.

ChromaDB stores, for every chunk:
    id         : "chunk-57"          (same chunk ID as in PostgreSQL)
    embedding  : [0.12, -0.04, ...]  (384 numbers from the embedding model)
    document   : the chunk text      (handy for debugging; PostgreSQL stays the source of truth)
    metadata   : document_id, access_level, department, title, page, section ...

The ACCESS LEVEL is stored on every chunk so that searches can be filtered
("only Public and Employee chunks") INSIDE ChromaDB, before any result comes back.
Similarity uses cosine distance: 0 = same meaning, 2 = opposite. similarity = 1 - distance.
"""

from pathlib import Path

from config import Config


def chunk_vector_id(chunk_id: int) -> str:
    return f"chunk-{chunk_id}"


class VectorStore:
    def __init__(self, path=None, collection_name=None):
        import chromadb
        from chromadb.config import Settings

        self.path = Path(path or Config.VECTOR_STORE_DIR)
        self.path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.path),
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
        self.collection_name = collection_name or Config.CHROMA_COLLECTION
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},  # compare vectors by angle (meaning)
            embedding_function=None,            # we always give our own embeddings
        )

    # ------------------------------------------------------------- write --

    def upsert_chunks(self, items):
        """
        items: list of dicts with keys
            chunk_id, embedding, content, document_id, chunk_index, access_level,
            department, document_title, doc_code, page_number, section_reference
        Upsert = insert, or replace if the ID already exists.
        """
        if not items:
            return
        self.collection.upsert(
            ids=[chunk_vector_id(i["chunk_id"]) for i in items],
            embeddings=[i["embedding"] for i in items],
            documents=[i["content"] for i in items],
            metadatas=[_metadata(i) for i in items],
        )

    def delete_document(self, document_id: int):
        """Remove every vector that belongs to one document."""
        self.collection.delete(where={"document_id": int(document_id)})

    def update_document_metadata(self, document_id: int, **changes):
        """
        Change metadata (e.g. access_level) on all chunks of a document, without re-embedding.
        Used when the admin changes a document's access level (Phase 7).
        """
        existing = self.collection.get(where={"document_id": int(document_id)}, include=["metadatas"])
        if not existing["ids"]:
            return 0
        new_metas = [{**m, **changes} for m in existing["metadatas"]]
        self.collection.update(ids=existing["ids"], metadatas=new_metas)
        return len(existing["ids"])

    def reset(self):
        """Delete ALL vectors (used by the rebuild script)."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}, embedding_function=None,
        )

    # -------------------------------------------------------------- read --

    def count(self) -> int:
        return self.collection.count()

    def count_for_document(self, document_id: int) -> int:
        return len(self.collection.get(where={"document_id": int(document_id)}, include=[])["ids"])

    def query(self, query_embedding, allowed_access_levels, top_k=5):
        """
        Find the chunks closest in meaning to the question, ONLY among chunks whose
        access_level is in allowed_access_levels. Returns a list of dicts, best first.
        """
        allowed = sorted(set(allowed_access_levels or []))
        if not allowed or top_k <= 0:
            return []  # no permissions = no results (fail closed)

        where = {"access_level": allowed[0]} if len(allowed) == 1 else {"access_level": {"$in": allowed}}
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["metadatas", "documents", "distances"],
        )
        hits = []
        for vid, meta, text, dist in zip(result["ids"][0], result["metadatas"][0],
                                         result["documents"][0], result["distances"][0]):
            hits.append({
                "vector_id": vid,
                "chunk_id": meta["chunk_id"],
                "document_id": meta["document_id"],
                "content": text,
                "score": round(1 - dist, 4),  # cosine similarity: 1 = same meaning
                "metadata": meta,
            })
        return hits


def _metadata(item):
    """ChromaDB metadata cannot hold None, so empty values are simply left out."""
    meta = {
        "chunk_id": int(item["chunk_id"]),
        "document_id": int(item["document_id"]),
        "chunk_index": int(item["chunk_index"]),
        "access_level": item["access_level"],
        "department": item["department"],
        "document_title": item["document_title"],
    }
    for key in ("doc_code", "section_reference"):
        if item.get(key):
            meta[key] = item[key]
    if item.get("page_number") is not None:
        meta["page_number"] = int(item["page_number"])
    return meta


# ----------------------------------------------------- shared instance --

_default_store = None


def get_vector_store() -> VectorStore:
    """The vector store used by the app (tests replace it with a temporary one)."""
    global _default_store
    if _default_store is None:
        _default_store = VectorStore()
    return _default_store


def set_vector_store(store):
    """Replace the shared store (used by tests)."""
    global _default_store
    _default_store = store
