from app.config import Settings
from app.embeddings.base import Embedder
from app.ingestion.chunker import chunk_document
from app.scraping.cleaner import HtmlCleaner
from app.scraping.crawler import Crawler
from app.scraping.fetchers import RequestsFetcher
from app.storage.stores import CleanStore, RawStore
from app.vectorstore.base import VectorStore


class IngestionPipeline:
    """scrape -> clean -> index. Cada etapa se puede ejecutar por separado."""

    def __init__(self, cfg: Settings, embedder: Embedder, store: VectorStore):
        self.cfg, self.embedder, self.store = cfg, embedder, store
        self.raw, self.clean = RawStore(cfg.raw_dir), CleanStore(cfg.clean_dir)

    def scrape(self):
        self.raw.clear()
        n = Crawler(RequestsFetcher(self.cfg.user_agent), self.raw, self.cfg).run()
        print(f"Scraping listo: {n} páginas en {self.cfg.raw_dir}")

    def clean_step(self):
        cleaner = HtmlCleaner()
        docs = [d for i, u, h in self.raw.iter_pages() if (d := cleaner.clean(i, u, h))]
        docs = cleaner.drop_boilerplate(docs)
        self.clean.clear()
        for d in docs:
            self.clean.save(d)
        print(f"Limpieza lista: {len(docs)} documentos en {self.cfg.clean_dir}")

    def index(self):
        chunks = [c for d in self.clean.iter_docs()
                  for c in chunk_document(d, self.cfg.chunk_size, self.cfg.chunk_overlap)]
        if not chunks:
            raise SystemExit("No hay documentos limpios. Ejecuta primero scrape y clean.")
        self.store.reset()
        self.store.add(chunks, self.embedder.embed_documents([c.text for c in chunks]))
        print(f"Indexado: {len(chunks)} chunks (total en índice: {self.store.count()})")

    def run_all(self):
        self.scrape(); self.clean_step(); self.index()
