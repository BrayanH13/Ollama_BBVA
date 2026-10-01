import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


def _b(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "si"}


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("BASE_URL", "https://www.bbva.com.co")
    max_pages: int = int(os.getenv("MAX_PAGES", "150"))
    request_delay: float = float(os.getenv("REQUEST_DELAY", "1.0"))
    user_agent: str = os.getenv("USER_AGENT", "bbva-rag-bot/1.0 (proyecto educativo)")

    data_dir: Path = Path(os.getenv("DATA_DIR", "data"))
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "900"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    top_k: int = int(os.getenv("TOP_K", "4"))

    history_window: int = int(os.getenv("HISTORY_WINDOW", "6"))
    rewrite_query: bool = _b("REWRITE_QUERY", "true")

    # ollama (por defecto, local y gratis) | openai (cualquier endpoint compatible) | anthropic (de pago)
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def clean_dir(self) -> Path:
        return self.data_dir / "clean"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def history_db(self) -> Path:
        return self.data_dir / "history.sqlite3"


@lru_cache
def get_settings() -> Settings:
    return Settings()
