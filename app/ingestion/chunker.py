from app.models import Chunk, Document


def split_text(text: str, size: int, overlap: int) -> list[str]:
    chunks, cur = [], ""
    for para in (p for p in text.split("\n") if p.strip()):
        if len(cur) + len(para) + 1 <= size:
            cur = f"{cur}\n{para}" if cur else para
            continue
        if cur:
            chunks.append(cur)
        tail = cur[-overlap:] if cur and overlap else ""
        cur = f"{tail}\n{para}" if tail else para
        while len(cur) > size * 1.5:          # párrafos gigantes
            chunks.append(cur[:size])
            cur = cur[size - overlap:]
    if cur:
        chunks.append(cur)
    return chunks


def chunk_document(doc: Document, size: int, overlap: int) -> list[Chunk]:
    return [Chunk(f"{doc.doc_id}-{i}", t, doc.url, doc.title)
            for i, t in enumerate(split_text(doc.text, size, overlap))]
