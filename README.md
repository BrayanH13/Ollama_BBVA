# Ollama_BBVA
asistente conversacional que permita a usuarios internos consultar información publicada en su sitio web institucional
# RAG sobre bbva.com.co (100% local: Ollama + ChromaDB)

## Arranque
```bash
cp .env.example .env
docker compose --profile ingest run --rm ingest   # scraping -> limpieza -> indexado
docker compose up -d --build                      # levanta Ollama, descarga el modelo y arranca la API
docker compose logs -f ollama-pull                # progreso de la descarga (solo la 1ª vez, ~4-5 GB)
```
Abre http://localhost:8000 cuando `ollama-pull` termine.

Etapas por separado: `docker compose --profile ingest run --rm ingest python -m app.cli scrape|clean|index`

## Modelo
`OLLAMA_MODEL` en `.env` (por defecto `qwen2.5:7b`; `llama3.2:3b` para menor uso de RAM).
Tras cambiarlo: `docker compose up -d` (se descarga el nuevo modelo).
`OLLAMA_CONTEXT_LENGTH` (8192) evita que Ollama trunque el prompt; `OLLAMA_KEEP_ALIVE` (30m) mantiene el modelo en memoria.
Con GPU NVIDIA descomenta el bloque `deploy` del servicio `ollama` en `docker-compose.yml`.

## Datos locales (`./data`)
- `raw/` HTML crudo + `index.jsonl`  · `clean/` JSON limpio por página
- `chroma/` índice vectorial  · `history.sqlite3` historial por conversation_id

## API
- `POST /api/chat {message, conversation_id?}` · `GET/DELETE /api/conversations/{id}` · `GET /api/health`
- `HISTORY_WINDOW` (N) controla cuántos mensajes previos se usan.

## Cambiar de proveedor, algunos como ejemplo 
`LLM_PROVIDER=ollama` (por defecto) · `openai` (cualquier endpoint compatible) · `anthropic` (de pago; descomenta `anthropic` en `requirements.txt`).
