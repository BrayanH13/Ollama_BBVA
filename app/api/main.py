import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.container import history_repo, rag_service, vector_store

app = FastAPI(title="BBVA Colombia RAG")
STATIC = Path(__file__).resolve().parent.parent / "static"


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    cfg = get_settings()
    return {"status": "ok", "indexed_chunks": vector_store().count(), "history_window": cfg.history_window}


@app.post("/api/chat")
def chat(body: ChatIn):
    if vector_store().count() == 0:
        raise HTTPException(409, "El índice está vacío. Ejecuta la ingesta primero.")
    try:
        return rag_service().chat(body.conversation_id or uuid.uuid4().hex, body.message.strip())
    except Exception as e:
        raise HTTPException(502, f"Error generando la respuesta: {e}")


@app.get("/api/conversations/{cid}")
def get_conversation(cid: str):
    return {"conversation_id": cid, "messages": history_repo().all(cid)}


@app.delete("/api/conversations/{cid}")
def delete_conversation(cid: str):
    history_repo().delete(cid)
    return {"deleted": cid}
