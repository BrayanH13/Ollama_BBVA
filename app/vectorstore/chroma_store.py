from pathlib import Path

import chromadb

from app.models import Chunk, Retrieved
from app.vectorstore.base import VectorStore

COLLECTION = "bbva_co"


class ChromaStore(VectorStore):
    def __init__(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(path))
        self.col = self._open()

    def _open(self):
        return self.client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    def reset(self):
        try:
            self.client.delete_collection(COLLECTION)
        except Exception:
            pass
        self.col = self._open()

    def add(self, chunks, embeddings):
        for i in range(0, len(chunks), 500):
            part = chunks[i:i + 500]
            self.col.add(
                ids=[c.chunk_id for c in part],
                documents=[c.text for c in part],
                embeddings=embeddings[i:i + 500],
                metadatas=[{"url": c.url, "title": c.title} for c in part],
            )

    def search(self, embedding, k):
        if self.col.count() == 0:
            return []
        r = self.col.query(query_embeddings=[embedding], n_results=k)
        return [Retrieved(text=d, url=m["url"], title=m["title"], score=1 - dist)
                for d, m, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0])]

    def count(self):
        return self.col.count()
