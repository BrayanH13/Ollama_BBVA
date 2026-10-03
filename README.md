# RAG sobre bbva.com.co (100% local: Ollama + ChromaDB)

Sistema de preguntas y respuestas sobre el contenido de https://www.bbva.com.co/. Obtiene las páginas del sitio,
guarda los datos crudos y limpios en local, los vectoriza en una base vectorial y expone un chat web minimalista con
historial por conversación. Todo corre en tu máquina con software abierto y sin costo por token.

## Índice
1. [Requisitos previos](#1-requisitos-previos)
2. [Puesta en marcha paso a paso](#2-puesta-en-marcha-paso-a-paso)
3. [Cómo usar la interfaz conversacional](#3-cómo-usar-la-interfaz-conversacional)
4. [Patrones de diseño](#4-patrones-de-diseño)
5. [Stack tecnológico y justificación](#5-stack-tecnológico-y-justificación)
6. [Limitaciones conocidas y decisiones de diseño](#6-limitaciones-conocidas-y-decisiones-de-diseño)
7. [Futuras mejoras](#7-futuras-mejoras)
8. [Referencia](#8-referencia-api-cli-datos-métricas-y-errores)

---

## 1. Requisitos previos

| Requisito | Detalle |
|---|---|
| **Docker** con **Docker Compose v2** | Docker Desktop (Windows/Mac) o Docker Engine + plugin compose (Linux). Comprueba con `docker compose version`. |
| **Git** | Para clonar el repositorio. |
| **Memoria RAM** | ~8 GB libres para `qwen2.5:7b` (por defecto). Con menos, usa `llama3.2:3b` (`OLLAMA_MODEL` en `.env`). |
| **Disco** | ~6 GB: el modelo de Ollama (~4-5 GB), la imagen de la API y el modelo de embeddings (~0,5 GB, se descarga al construir la imagen). |
| **Internet** | Solo en la primera construcción (imágenes, modelo del LLM y de embeddings) y para el scraping. Después el chat funciona sin conexión. |
| **GPU** (opcional) | NVIDIA acelera mucho las respuestas: descomenta el bloque `deploy` del servicio `ollama` en `docker-compose.yml`. |
| **API keys** | **Ninguna** con la configuración por defecto. Solo si cambias a `openai` o `anthropic` (de pago, opcional). |

### Variables de entorno
Se definen en `.env` (se crea copiando `.env.example`, que trae valores por defecto funcionales y cada variable comentada).
No necesitas editar nada para arrancar. Las más relevantes:

| Variable | Defecto | Para qué sirve |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` (local, gratis), `openai` (endpoint compatible) o `anthropic` (de pago). |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Modelo local. `llama3.2:3b` si tienes poca RAM. |
| `OLLAMA_CONTEXT_LENGTH` | `8192` | Contexto del modelo; evita que Ollama trunque el prompt. |
| `OLLAMA_KEEP_ALIVE` | `30m` | Tiempo que el modelo se mantiene cargado en memoria. |
| `LLM_TIMEOUT` | `300` | Segundos máximos esperando al modelo (en CPU puede tardar). |
| `HISTORY_WINDOW` | `6` | **N**: cuántos mensajes previos de la conversación se envían al modelo. |
| `TOP_K` | `4` | Fragmentos recuperados por pregunta. |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `900` / `150` | Tamaño y solapamiento de los fragmentos (caracteres). |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Modelo de embeddings (multilingüe, local). |
| `REWRITE_QUERY` | `true` | Reformula preguntas de seguimiento (una llamada extra al LLM; `false` si va lento). |
| `BASE_URL` / `MAX_PAGES` / `REQUEST_DELAY` | sitio / `150` / `1.0` | Alcance y ritmo del scraping. |
| `LOCAL_DOCS_DIR` | `../Database-HTML_BBVA` | Carpeta con HTML guardado a mano para la ingesta local. |
| `RATE_LIMIT_PER_MIN` | `20` | Preguntas por minuto y por IP (0 = sin límite). |
| `METRICS_TOKEN` | vacío | Si se define, protege `/api/metrics*`. |
| `REPORT_TZ`, `IMPACT_MINUTES_PER_ANSWER`, `IMPACT_COST_PER_MINUTE` | `America/Bogota`, `5`, `0` | Zona horaria y supuestos del valor de impacto ([docs/METRICS.md](docs/METRICS.md)). |

> Pon los comentarios del `.env` en una línea aparte, no al final del valor.

---

## 2. Puesta en marcha paso a paso

**1. Clonar el repositorio**
```bash
git clone <URL-DEL-REPOSITORIO> bbva-rag
cd bbva-rag
```

**2. Configurar el entorno**
```bash
cp .env.example .env        # Windows (cmd): copy .env.example .env
```
Ajusta `OLLAMA_MODEL` si tu equipo tiene poca RAM; el resto puede quedar igual.

**3. Cargar los datos del sitio (ingesta)** — elige una vía:

*a) Scraping directo* (scraping → limpieza → indexado):
```bash
docker compose --profile ingest run --rm ingest
```
*b) Si el sitio responde `403` al bot* (bloquea scrapers): guarda las páginas desde tu navegador
(`Ctrl+S` > "Página web, completa") en una carpeta, apunta `LOCAL_DOCS_DIR` en `.env` a ella y ejecuta:
```bash
docker compose --profile ingest run --rm ingest python -m app.cli local
```
Reutiliza la misma limpieza, chunker, embeddings e índice, y guarda el HTML original en `data/raw/`.

**4. Levantar el sistema**
```bash
docker compose up -d --build
docker compose logs -f ollama-pull     # progreso de la descarga del modelo (solo la 1ª vez, ~4-5 GB)
```
Se inician `ollama` (LLM), `ollama-pull` (descarga el modelo) y `api` (que espera a que la descarga termine).

**5. Verificar**
```bash
curl http://localhost:8000/api/health
```
Debe mostrar `"status":"ok"` y `indexed_chunks` mayor que 0. Si el estado es `degraded`: el índice está vacío (repite el paso 3)
o el modelo aún se está descargando.

**6. Abrir** http://localhost:8000

**Operación diaria**
- Detener: `docker compose down` (los datos y el historial se conservan en `./data` y en el volumen `ollama`).
- Arrancar de nuevo: `docker compose up -d` (no hace falta reconstruir ni reindexar).
- Si agregas más datos: ejecuta de nuevo el paso 3. **No hace falta reiniciar la API**: reabre el índice sola.
- Logs: `docker compose logs --tail 50 api`.

**Solución de problemas**
- `ollama-pull` falla con *network is unreachable* (IPv6): descarga el modelo con `docker compose exec ollama ollama pull qwen2.5:7b`
  o desactiva IPv6 en el servicio `ollama` (`sysctls: net.ipv6.conf.all.disable_ipv6: "1"`).
- El chat dice que no encontró información: revisa el retrieval con `search` (sección 8).
- `docker compose build` falla leyendo `.env`: revisa que no haya comentarios al final de las líneas.

---

## 3. Cómo usar la interfaz conversacional

Abre http://localhost:8000.

- **Preguntar:** escribe en el cuadro inferior y pulsa Enter. La respuesta se basa solo en el contenido indexado del sitio y
  muestra las **fuentes** (páginas usadas). Si el sitio no contiene la respuesta, el asistente lo dice en lugar de inventarla.
- **Conversación e historial:** cada conversación tiene un ID. El asistente recuerda los últimos `HISTORY_WINDOW` mensajes,
  por lo que se pueden hacer preguntas de seguimiento ("¿y cuáles son los requisitos?").
- **Barra lateral:** lista las conversaciones guardadas; haz clic en una para retomarla. El botón **Nueva conversación**
  (arriba) inicia otra. El historial persiste aunque se reinicie la API. Para borrar una conversación usa la API
  (`DELETE /api/conversations/{id}`).
- **Valoración:** 👍 / 👎 en cada respuesta alimentan las métricas.
- **Métricas:** http://localhost:8000/metrics (preguntas, tasa de respuesta, latencia, satisfacción, temas frecuentes y valor
  de impacto estimado, con exportación a CSV).
- **Errores:** si el modelo no está disponible verás el mensaje "Estamos teniendo dificultades técnicas. Pronto estaremos
  contigo nuevamente."; el detalle queda en los logs.
- **Por API**, sin interfaz:
```bash
curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" \
  -d '{"message":"¿Qué requisitos tiene un crédito hipotecario?","conversation_id":"mi-id"}'
```

---

## 4. Patrones de diseño

```
Interfaz web ─► FastAPI ─► RagService (Facade) ─┬─► Embedder ────► VectorStore ──► Chroma
                                                ├─► HistoryRepository ─► SQLite
                                                └─► LLMClient ───► Ollama / OpenAI / Anthropic
Ingesta:  IngestionPipeline (Facade) ─► Fetcher ─► RawStore ─► HtmlCleaner ─► CleanStore ─► chunker ─► VectorStore
```

Las dependencias se construyen en un único lugar (`app/container.py`) y las clases reciben lo que necesitan por constructor.

### Creacionales
| Patrón | Dónde | Por qué |
|---|---|---|
| **Factory** (Simple Factory) | `app/llm/factory.py` → `create_llm()` | Elige el cliente (Ollama, OpenAI o Anthropic) según `LLM_PROVIDER`. El resto del sistema pide un `LLMClient` y no sabe cuál concreto recibe. Es una fábrica en forma de función, no el *Factory Method* clásico con subclases. |
| **Singleton** (vía `lru_cache`) | `app/container.py` (`embedder()`, `vector_store()`, `rag_service()`) y `config.get_settings()` | Cargar el modelo de embeddings y abrir Chroma/SQLite es costoso y debe ocurrir una sola vez por proceso. Se usa caché de módulo en lugar de una clase con constructor privado: es lo idiomático en Python y se puede reiniciar en pruebas con `cache_clear()`. |

### Estructurales
| Patrón | Dónde | Por qué |
|---|---|---|
| **Facade** | `RagService.chat()` (`app/rag/service.py`) e `IngestionPipeline` (`app/ingestion/pipeline.py`) | La API solo llama `chat(id, pregunta)`: no conoce el historial, la reescritura de la consulta, los embeddings, la búsqueda, el armado del prompt ni el LLM. Igual la ingesta: `run_all()` o `ingest_local()` esconden crawler, limpieza, chunker, embeddings e índice, y la CLI queda trivial. |
| **Adapter** | `OpenAICompatClient` y `AnthropicClient` (→ `LLMClient`), `FastEmbedEmbedder` (→ `Embedder`), `ChromaStore` (→ `VectorStore`) | Cada librería habla su propio idioma: fastembed devuelve arrays de numpy, Chroma devuelve distancias, Anthropic usa un SDK y Ollama una API HTTP. Los adaptadores lo traducen a interfaces propias (listas de números, `score = 1 - distancia`, texto), de modo que el núcleo no depende de ningún proveedor. |

### Comportamentales
| Patrón | Dónde | Por qué |
|---|---|---|
| **Strategy** | `Fetcher` (`app/scraping/fetchers.py`) y `LLMClient` (`app/llm/clients.py`); también `Embedder`, `VectorStore` y `HistoryRepository` | El algoritmo intercambiable se inyecta por constructor. Añadir Ollama solo requirió una rama en la fábrica y variables en `config.py`, sin tocar `RagService`. Si el sitio necesitara JavaScript, bastaría un `PlaywrightFetcher` sin tocar `Crawler`. |

### Otros patrones arquitectónicos (no pertenecen al catálogo GoF)
| Patrón | Dónde | Por qué |
|---|---|---|
| **Repository** | `RawStore`, `CleanStore` (`app/storage/stores.py`) y `HistoryRepository` (`app/history/repository.py`) | Encapsulan el acceso a disco y a SQLite. El resto del código trabaja con `Document` o mensajes, no con rutas ni SQL; cambiar SQLite por otra base sería escribir otra implementación de `HistoryRepository`. |
| **Dependency Injection + Composition Root** | `app/container.py` | Un solo lugar construye y conecta todo. Como las clases reciben sus dependencias, se pueden probar sustituyéndolas por dobles falsos (sin Ollama, sin Chroma, sin descargar modelos). |
| **Pipeline** | `scrape → clean → index` (o `local → clean → index`) | Cada etapa se ejecuta por separado y deja su resultado en disco (`data/raw` → `data/clean` → `data/chroma`), por lo que se puede repetir una sola etapa sin rehacer las anteriores. |
| **DTO** | `Document`, `Chunk`, `Retrieved` (`app/models.py`) | Dataclasses sin lógica que transportan datos entre capas con un formato único. |
| **Retry con espera exponencial** | `app/utils/retry.py` (usado por el cliente del LLM y el scraper) | Los fallos de red y los 5xx suelen ser transitorios; reintentar con esperas crecientes evita caídas innecesarias. Los errores definitivos (p. ej. modelo no descargado) no se reintentan. |
| **Rate limiter (ventana deslizante)** | `app/api/ratelimit.py` | Protege al LLM local, que es el recurso escaso, de ráfagas de peticiones por IP (responde 429 con `Retry-After`). |
| **Jerarquía de excepciones tipadas** | `app/errors.py` | Cada falla tiene un `user_message` (lo que ve el usuario) y un `detail` (solo logs), de modo que la interfaz nunca expone detalles técnicos. |

**Principios que sostienen lo anterior:** inversión de dependencias (el núcleo depende de interfaces abstractas, no de Chroma ni de Ollama) y abierto/cerrado (se añaden proveedores sin modificar el código existente).
No se usaron otros patrones (Observer, Decorator, etc.) porque el proyecto no tiene un problema que resuelvan; añadirlos sería sobreingeniería.

---

## 5. Stack tecnológico y justificación

| Componente | Elección | Por qué |
|---|---|---|
| Contenedores | **Docker + Docker Compose** | Reproducible: un comando levanta LLM, API e ingesta sin instalar nada más. |
| LLM | **Ollama** con `qwen2.5:7b` | Open source, local y sin costo por token; buen español. Es intercambiable (`LLM_PROVIDER`) por cualquier endpoint compatible con OpenAI o por Anthropic. |
| Embeddings | **fastembed** + `paraphrase-multilingual-MiniLM-L12-v2` (384 d) | Multilingüe (el sitio está en español), corre en CPU vía ONNX sin PyTorch y se descarga al construir la imagen, así que en ejecución no depende de internet. |
| Base vectorial | **ChromaDB** (embebida, persistente, distancia coseno) | Sin servidor adicional que operar; persiste en `data/chroma`. Suficiente para un sitio de cientos o pocos miles de fragmentos. |
| API | **FastAPI + Uvicorn** | Tipado con Pydantic, documentación automática en `/docs` y rendimiento de sobra para este uso. |
| Scraping y limpieza | **requests + BeautifulSoup4 + lxml** | Ligeros y suficientes para HTML estático; el rastreo respeta un retardo entre peticiones. |
| Historial | **SQLite** | Sin servicio extra, transaccional y en un único archivo (`data/history.sqlite3`). Detrás de la interfaz `HistoryRepository`. |
| Interfaz | **HTML + JavaScript plano** | Minimalista y sin build ni dependencias de frontend, como pedía el enunciado. |
| Zona horaria | **tzdata** | Para que las métricas por día usen `REPORT_TZ` también dentro del contenedor. |

---

## 6. Limitaciones conocidas y decisiones de diseño

**Decisiones de diseño**
- **Todo local y open source:** prima el costo cero y la privacidad sobre la calidad de un modelo comercial.
- **Respuestas ancladas al contenido:** el prompt exige responder solo con los fragmentos recuperados y citar fuentes.
- **Recuperación con varias consultas:** se busca con la pregunta original y con una versión reformulada (usa el historial),
  se fusionan por mejor puntaje y se conservan `TOP_K`. El título de la página se antepone solo para generar el embedding.
- **Contexto acotado:** fragmentos e historial se recortan para caber en `OLLAMA_CONTEXT_LENGTH`.
- **Ingesta en etapas** (`raw → clean → chroma`), cada una repetible por separado y sin reemplazar datos buenos por malos.
- **Los fallos técnicos no se guardan** en el historial, por lo que tampoco aparecen en las métricas.

**Limitaciones**
- **Sin autenticación ni usuarios:** cualquiera con acceso a la URL ve **todas** las conversaciones y puede borrarlas. El ID de
  conversación no es un secreto. Solo las métricas se pueden proteger con `METRICS_TOKEN`. No exponer a internet tal cual.
- **Bloqueo anti-bot:** el sitio puede responder 403 al scraper; la alternativa es la ingesta local de HTML guardado a mano.
- **Páginas con JavaScript:** solo se lee el HTML recibido; el contenido que se pinta con JS (calculadoras, simuladores) no se captura.
- **Reindexado completo:** cada ingesta reconstruye el índice; no hay actualización incremental ni detección de cambios.
- **Sin reranker:** la recuperación usa solo similitud vectorial; con preguntas ambiguas puede traer fragmentos poco relevantes.
- **Latencia del LLM local:** en CPU una respuesta puede tardar decenas de segundos o minutos; sin GPU conviene un modelo más pequeño.
- **Sin streaming:** la respuesta aparece completa al terminar de generarse.
- **Calidad del modelo:** un modelo de 7B puede equivocarse o ignorar parte del contexto; las fuentes permiten verificarlo.
- **Métricas heurísticas:** "respondida" se infiere (por ejemplo, si el asistente indicó que no encontró información) y el
  **valor de impacto es una estimación** basada en supuestos configurables (`IMPACT_*`), no un resultado medido.
- **Límite por IP:** en Docker Desktop todas las peticiones llegan con la misma IP, así que el límite es efectivamente global.
- **Pruebas:** hay pruebas offline de manejo de errores y métricas con componentes simulados; no hay suite de integración
  automatizada contra Ollama/Chroma reales.

---

## 7. Futuras mejoras

- **Autenticación y aislamiento por usuario** (cada quien ve solo sus conversaciones) y HTTPS detrás de un proxy.
- **Reranker open source** (cross-encoder con licencia permisiva) sobre los candidatos de Chroma para mejorar la precisión.
- **Búsqueda híbrida** (BM25 + vectorial) para términos exactos como nombres de productos o cifras.
- **Respuestas en streaming** (SSE) para percibir menos latencia.
- **Ingesta incremental** con hash del contenido y reindexado solo de páginas cambiadas, programada periódicamente.
- **Renderizado de JavaScript** (un `PlaywrightFetcher` encaja en la interfaz `Fetcher` sin tocar el crawler).
- **Evaluación automática de calidad** con un conjunto de preguntas de referencia y métricas de recuperación (recall@k).
- **Pruebas de integración en CI** con Docker y observabilidad (métricas Prometheus, trazas).
- **Gestión de conversaciones:** títulos editables, búsqueda en el historial y exportación.

---

## 8. Referencia: API, CLI, datos, métricas y errores

### API
| Endpoint | Descripción |
|---|---|
| `GET /` | Interfaz de chat. |
| `POST /api/chat` | `{message, conversation_id?}` → respuesta, fuentes e ID de conversación. |
| `GET /api/conversations` | Lista de conversaciones (`conversation_id`, `title`). |
| `GET /api/conversations/{id}` · `DELETE /api/conversations/{id}` | Ver o borrar una conversación. |
| `POST /api/messages/{message_id}/feedback` | Valoración 👍/👎 de una respuesta. |
| `GET /api/health` | Estado, `indexed_chunks` y disponibilidad del modelo (`llm`). |
| `GET /metrics` · `GET /api/metrics` · `GET /api/metrics/export.csv` | Panel, datos y exportación de métricas. |

`HISTORY_WINDOW` (N) controla cuántos mensajes previos se usan. Documentación interactiva en http://localhost:8000/docs.

### CLI (`python -m app.cli`)
`scrape | clean | index | all | local [carpeta] | docs | show <fragmento> | search "pregunta"`, por ejemplo:
```bash
docker compose --profile ingest run --rm ingest python -m app.cli search "crédito hipotecario"
```
- `docs`: páginas limpias · `show`: texto indexado de una página · `search`: fragmentos y puntajes que recibiría el LLM.

### Datos locales (`./data`)
- `raw/` HTML crudo + `index.jsonl` · `clean/` JSON limpio por página
- `chroma/` índice vectorial · `history.sqlite3` historial por conversation_id · `import_errors.log` archivos que no se pudieron procesar

### Modelo y proveedor
- `OLLAMA_MODEL` en `.env`; tras cambiarlo ejecuta `docker compose up -d` para que se descargue el nuevo modelo.
- `LLM_PROVIDER=ollama` (por defecto) · `openai` (cualquier endpoint compatible) · `anthropic` (de pago; descomenta `anthropic` en `requirements.txt`).

### Métricas del histórico
Panel en `/metrics`, API `/api/metrics`, export CSV y reporte por consola (`python -m app.analytics.report`).
Definiciones y supuestos del valor de impacto en [docs/METRICS.md](docs/METRICS.md).

### Errores y robustez
- **Chat:** el cliente del LLM reintenta con espera exponencial ante servicio caído o errores 5xx. Ante cualquier falla
  (Ollama caído, modelo no descargado, error interno, configuración) el usuario ve un único mensaje profesional
  ("Estamos teniendo dificultades técnicas. Pronto estaremos contigo nuevamente."; se cambia en `app/errors.py` y en
  `app/static/index.html`). Si el modelo es lento verá un aviso de demora. El detalle técnico queda solo en los logs:
  `docker compose logs --tail 30 api`.
- **Límite de peticiones:** `RATE_LIMIT_PER_MIN` (por IP). Responde 429 con `Retry-After`.
- **`GET /api/health`:** `status` pasa a `degraded` si el índice está vacío o el modelo no está listo.
- **Scraping:** reintentos ante fallos de red, 429 y 5xx. Si el sitio bloquea al bot, se detiene y **no reemplaza** `raw/` ni
  `clean/`; los datos nuevos se construyen en una carpeta temporal y solo reemplazan a los anteriores si salió bien.
- **Carga local y limpieza:** un archivo defectuoso no detiene el proceso; los errores quedan en `data/import_errors.log`.
- **Indexado:** los embeddings se calculan antes de tocar el índice; tras reindexar la API reabre la colección sola.
- **`.env`:** los comentarios en la misma línea del valor no rompen el arranque (aun así, ponlos en una línea aparte).
