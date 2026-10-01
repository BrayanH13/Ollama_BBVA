from dataclasses import dataclass, asdict


@dataclass
class Document:
    doc_id: str
    url: str
    title: str
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Chunk:
    chunk_id: str
    text: str
    url: str
    title: str


@dataclass
class Retrieved:
    text: str
    url: str
    title: str
    score: float
