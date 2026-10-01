from app.config import Settings
from app.embeddings.base import Embedder
from app.history.repository import HistoryRepository
from app.llm.clients import LLMClient
from app.vectorstore.base import VectorStore

SYSTEM = """Eres un asistente virtual que responde preguntas sobre el sitio web de BBVA Colombia.
Reglas:
- Responde SOLO con la información del CONTEXTO provisto. Si no está allí, di que no encontraste esa información en el sitio.
- Responde en español, de forma clara y concisa.
- Cita las fuentes con su número entre corchetes, por ejemplo [1].
- No inventes tasas, costos, requisitos ni fechas. No des asesoría financiera personalizada."""

REWRITE_SYSTEM = ("Reescribe la última pregunta del usuario como una pregunta autónoma en español, "
                  "usando el historial para resolver referencias. Responde SOLO con la pregunta.")


class RagService:
    """Patrón Facade: una sola entrada (chat) que orquesta historial, retrieval y LLM."""

    def __init__(self, cfg: Settings, embedder: Embedder, store: VectorStore,
                 llm: LLMClient, history: HistoryRepository):
        self.cfg, self.embedder, self.store, self.llm, self.history = cfg, embedder, store, llm, history

    @staticmethod
    def _window(msgs: list[dict]) -> list[dict]:
        while msgs and msgs[0]["role"] != "user":   # la API exige empezar con 'user'
            msgs = msgs[1:]
        return msgs

    def _standalone_query(self, question: str, past: list[dict]) -> str:
        if not (self.cfg.rewrite_query and past):
            return question
        try:
            q = self.llm.generate(REWRITE_SYSTEM, [*past, {"role": "user", "content": question}], 200)
            return q.strip() or question
        except Exception:
            return question

    def chat(self, conversation_id: str, question: str) -> dict:
        past = self._window(self.history.last(conversation_id, self.cfg.history_window))
        query = self._standalone_query(question, past)
        hits = self.store.search(self.embedder.embed_query(query), self.cfg.top_k)

        context = "\n\n".join(f"[{i}] {h.title} ({h.url})\n{h.text}" for i, h in enumerate(hits, 1)) \
            or "(sin resultados)"
        user_msg = f"CONTEXTO:\n{context}\n\nPREGUNTA: {question}"
        answer = self.llm.generate(SYSTEM, [*past, {"role": "user", "content": user_msg}])

        self.history.add(conversation_id, "user", question)
        self.history.add(conversation_id, "assistant", answer)
        sources, seen = [], set()
        for h in hits:
            if h.url not in seen:
                seen.add(h.url)
                sources.append({"title": h.title, "url": h.url, "score": round(h.score, 3)})
        return {"conversation_id": conversation_id, "answer": answer, "sources": sources}
