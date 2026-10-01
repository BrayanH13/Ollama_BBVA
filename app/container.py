"""Composition root: único lugar donde se construyen e inyectan las dependencias
(Factory + Singleton vía lru_cache)."""
from functools import lru_cache

from app.config import get_settings
from app.embeddings.fastembed_embedder import FastEmbedEmbedder
from app.history.repository import SqliteHistoryRepository
from app.ingestion.pipeline import IngestionPipeline
from app.llm.factory import create_llm
from app.rag.service import RagService
from app.vectorstore.chroma_store import ChromaStore


@lru_cache
def embedder():
    return FastEmbedEmbedder(get_settings().embedding_model)


@lru_cache
def vector_store():
    return ChromaStore(get_settings().chroma_dir)


def ingestion_pipeline() -> IngestionPipeline:
    return IngestionPipeline(get_settings(), embedder(), vector_store())


@lru_cache
def rag_service() -> RagService:
    cfg = get_settings()
    return RagService(cfg, embedder(), vector_store(), create_llm(cfg),
                      SqliteHistoryRepository(cfg.history_db))


@lru_cache
def history_repo():
    return rag_service().history
