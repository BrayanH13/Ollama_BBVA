from fastembed import TextEmbedding

from app.embeddings.base import Embedder


class FastEmbedEmbedder(Embedder):
    """Embeddings locales (ONNX, sin torch) y multilingües: sirve bien para español."""

    def __init__(self, model_name: str):
        self.model = TextEmbedding(model_name)

    def embed_documents(self, texts):
        return [v.tolist() for v in self.model.embed(texts, batch_size=32)]

    def embed_query(self, text):
        return next(iter(self.model.embed([text]))).tolist()
