"""Patrón Repository: encapsulan el acceso al disco (crudo y limpio)."""
import hashlib
import json
import time
from pathlib import Path
from typing import Iterator

from app.models import Document


def url_id(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:16]


class RawStore:
    """HTML tal cual fue descargado + un índice JSONL con metadatos."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.index = root / "index.jsonl"

    def save(self, url: str, html: str, status: int) -> str:
        doc_id = url_id(url)
        (self.root / f"{doc_id}.html").write_text(html, encoding="utf-8")
        with self.index.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"doc_id": doc_id, "url": url, "status": status,
                                "fetched_at": time.time()}) + "\n")
        return doc_id

    def iter_pages(self) -> Iterator[tuple[str, str, str]]:
        """Devuelve (doc_id, url, html); si una URL se descargó varias veces, gana la última."""
        if not self.index.exists():
            return
        latest = {}
        for line in self.index.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            latest[rec["doc_id"]] = rec
        for doc_id, rec in latest.items():
            p = self.root / f"{doc_id}.html"
            if p.exists():
                yield doc_id, rec["url"], p.read_text(encoding="utf-8")

    def clear(self):
        for p in self.root.glob("*"):
            p.unlink()


class CleanStore:
    """Documentos ya limpios en JSON (uno por página)."""

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, doc: Document):
        (self.root / f"{doc.doc_id}.json").write_text(
            json.dumps(doc.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def iter_docs(self) -> Iterator[Document]:
        for p in sorted(self.root.glob("*.json")):
            yield Document(**json.loads(p.read_text(encoding="utf-8")))

    def clear(self):
        for p in self.root.glob("*.json"):
            p.unlink()
