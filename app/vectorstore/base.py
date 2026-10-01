from abc import ABC, abstractmethod

from app.models import Chunk, Retrieved


class VectorStore(ABC):
    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None: ...

    @abstractmethod
    def search(self, embedding: list[float], k: int) -> list[Retrieved]: ...

    @abstractmethod
    def count(self) -> int: ...
