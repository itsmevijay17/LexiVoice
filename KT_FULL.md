# LexiVoice — Full Technical KT (Handover)

Version: 1.0
Date: 2025-12-09
Author: GitHub Copilot (prepared for Vijay)

Purpose
-------
This document is a complete technical Knowledge Transfer (KT) + operational guide for LexiVoice — an AI-powered multilingual legal assistant. It explains the codebase, runtime behavior, data formats, operational instructions, troubleshooting steps, extension points, and where to look for each implementation detail. It is written so a developer unfamiliar with the project can take over and operate/extend it.

Repository layout (top-level)
-----------------------------
- `backend/` — FastAPI backend code (main app, core modules, routers, scripts)
- `frontend/` — Streamlit frontend app and pages
- `backend/data/` — persisted data: `laws/`, `faiss_indexes/`, `audio/`, `processing_stats.json`
- `backend/models/` — local cached embedding model (e5-large), onnx/openvino artifacts
- `scripts/` — e2e tests and utilities
- `requirements.txt` — Python dependencies
- `README.md`, `setup_instructions.md`, `KT_ANALYSIS_DISCREPANCIES.md` — docs

High-level system architecture
------------------------------
User → (Streamlit UI) → Backend FastAPI endpoints

Text flow (simplified):
- Text query → `POST /api/v1/chat` → `chat` router → `retriever` (FAISS) → `llm_handler` (Groq) → format → optionally TTS → response

Voice flow (simplified):
- Upload voice → `POST /api/v1/chat/voice` → `speech_to_text` (Groq/Whisper) → same RAG pipeline → optionally TTS → response

Key technologies
----------------
- Backend: Python 3.11+, FastAPI, uvicorn
- Frontend: Streamlit
- Embeddings: `intfloat/multilingual-e5-large` via `sentence-transformers`
- Vector DB: FAISS (per-country `.faiss` files)
- LLM & STT provider: Groq (Groq client used in code)
- TTS: gTTS
- DB: MongoDB (pymongo)

How to run locally (development)
--------------------------------
Prereqs (Windows PowerShell):
- Python 3.10+ (venv recommended)
- Git
- MongoDB accessible (local or hosted) and `.env` prepared

1. Create and activate venv:

```powershell
python -m venv venv
& .\venv\Scripts\Activate.ps1
```

2. Install dependencies (from repo root):

```powershell
pip install -r requirements.txt
```

3. Create `.env` in repo root with keys (example):

```
GROQ_API_KEY=your_groq_key
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=lexivoice
ENVIRONMENT=development
```

4. Start backend (development):

```powershell
# from repo root
uvicorn backend.main:app --reload --log-level debug --access-log
```

5. Start frontend (Streamlit):

```powershell
cd frontend
streamlit run app.py
```

Repository walkthrough — core backend modules
-------------------------------------------
This section describes the main backend modules, their responsibilities, and key functions with file references.

1) `backend/main.py` — FastAPI app entrypoint
- Contains `lifespan` async context manager which:
  - Connects to MongoDB (`Database.connect_db()`)
  - Calls `preload_retrievers()` to schedule background FAISS loads
- Registers routers: `chat`, `feedback`
- Health and stats endpoints at `/health` and `/api/v1/stats`

Important: The startup currently preloads FAISS retrievers using `preload_retrievers()` in `backend/core/retriever.py`. This schedules index loads into a thread pool to avoid blocking the event loop during large index loads.

2) `backend/core/embeddings.py` — Embedding model wrapper
- Class: `EmbeddingModel`
  - Default model name used: `intfloat/multilingual-e5-large`
  - Local model path: `backend/models/e5-large` (downloaded on first run and re-used later)
  - API used: `sentence_transformers.SentenceTransformer`
  - Main methods:
    - `encode_texts(texts, show_progress=True) -> np.ndarray` (batch encoding, normalized)
    - `encode_single(text) -> np.ndarray`
    - `get_dimension()`
- Singleton accessor: `get_embedding_model()` to avoid repeated model loading

Notes:
- `normalize_embeddings=True` is used. With normalized vectors, FAISS L2 distance is equivalent to cosine similarity.
- Model dimension is 384.

3) `backend/core/document_processor.py` — Document parsing and chunking
- Class: `DocumentProcessor(chunk_size=500)`
  - Loads JSON files from `backend/data/laws/{country}.json`
  - Splits documents into chunks with metadata (title, section, chunk_id, total_chunks, category, source_url)
  - Preferred strategy: sentence-based chunking with `chunk_size=500` and `overlap=50` (configurable)
- Output: `DocumentChunk` dataclass instances used by retriever builder

4) `backend/core/retriever.py` — FAISS retriever
- Class: `FAISSRetriever(country)`
  - Paths: `backend/data/faiss_indexes/{country}.faiss` and `{country}_metadata.pkl`
  - `build_index()`:
    - Uses `DocumentProcessor` → get chunks
    - Uses EmbeddingModel to encode chunk texts
    - Builds a `faiss.IndexFlatL2(dimension)` and `index.add(embeddings)`
    - Saves `faiss.write_index(self.index, self.index_path)` and pickled metadata
  - `load_index()`:
    - Reads index with `faiss.read_index(...)` and loads metadata pickle
    - In our patch, it's protected by a lock and handles exceptions gracefully (leaves index `None` on error)
  - `search(query, top_k=3)`: encode query via embedding model, `index.search(...)`, map indices back to metadata, compute similarity as `1/(1+distance)`
  - `get_retriever(country)` global factory caches `FAISSRetriever` instances
- Module-level executor: a `ThreadPoolExecutor` is used and `preload_retrievers()` helper schedules background loads at app startup

Important operational notes:
- Index building is CPU- and memory-bound — prefer running `backend/scripts/build_vector_store.py` offline (not on request path) to produce `.faiss` files.
- The repo contains `backend/data/faiss_indexes/*.faiss` files; current sizes found were ~0.35 MB each (small), so they are inexpensive to load.

5) `backend/core/llm_handler.py` — LLM orchestration
- Class: `LLMHandler`
  - Uses Groq client: `Groq(api_key=...)`
  - Configured with `model = "llama-3.1-8b-instant"`, `max_tokens=1000`, `temperature=0.3`
  - `create_prompt(query, retrieved_chunks, country)` formats context and the JSON-constrained instructions for the model output
  - `generate_answer(query, retrieved_chunks, country)` calls the Groq API and parses JSON output (answer, reasoning, sources, confidence)

IMPORTANT: KT doc earlier stated `llama-3.1-70b-versatile`. The code uses `8b-instant`. If you need higher reasoning fidelity, change the model id or provider settings and consider cost/perf tradeoffs.

6) `backend/core/speech_to_text.py` — STT via Groq Whisper
- `SpeechToTextHandler` uses Groq Whisper model: `whisper-large-v3-turbo`
- Validates audio formats and file size (limit 25 MB)
- Calls Groq STT API
- Post-processes transcription: detects empty/punctuation-only transcriptions and returns `success: False` in those cases

7) `backend/core/text_to_speech.py` — TTS via gTTS
- `TextToSpeechHandler` wraps gTTS with caching and language mapping
- Audio files cached under `backend/data/audio/` (filenames hashed by text + language)
- Supports returning either `audio_path` or `audio_base64`
- `language_map` includes many ISO 639-1 codes; `country_language_map` defaults to `en` for `india`, `canada`, `usa`

8) `backend/core/translator.py` — Translation layer
- `TranslationHandler` implements a resilient translation system:
  - Tries `googletrans` (`googletrans==4.0.0-rc1`) top-level import
  - If not available, dynamic import attempted; if still missing, falls back to `deep-translator` (requests-based)
  - `detect_language(text)` and `translate_text(text, target_lang='en')` helpers
- Although KT envisions using multilingual embeddings (E5) to skip query translation, current code still uses the translator in `chat` router to optionally translate query and answers. This is a key divergence: the system currently runs a hybrid flow (translation + multilingual embeddings) in places.

9) `backend/core/crud.py` — Database CRUD
- `QueryLogCRUD` and `FeedbackCRUD` implement create/read functions for query logs and feedback
- No `User` CRUD functions are implemented (no user collection in code). Auth router is empty. So authentication is frontend/demo-only.

10) `backend/routers/chat.py` — Main RAG router
- `POST /api/v1/chat`: main flow
  - Optional translation of query to English (if `request.user_language != 'en'`) via `get_translator()`
  - Calls `get_retriever(country)` and `retriever.search(query_for_rag, top_k=3)`
  - Calls `get_llm_handler()` and `llm.generate_answer(...)`
  - Optionally translate answer back to user language
  - Optionally generate TTS audio via `get_tts_handler().convert_answer_to_audio()`
  - Saves query log via `QueryLogCRUD.create_query_log`
- `POST /api/v1/chat/voice`: similar but accepts uploaded audio, calls STT, builds ChatRequest, and runs same pipeline

11) `backend/routers/feedback.py` — Feedback endpoints
- `POST /api/v1/feedback` — save rating & comment — checks query exists, avoids duplicates
- `GET /api/v1/feedback/stats` — collects overall feedback stats

12) `backend/scripts/build_vector_store.py` — offline index builder
- Iterates countries `['india','canada','usa']`, constructs `FAISSRetriever(country)` and calls `build_index()` to create `.faiss` files and metadata
- This is how you should produce production-ready vector stores after adding/updating documents

13) `backend/data/laws/` — Document storage
- Files: `india.json`, `canada.json`, `usa.json`
- Expected JSON structure for each law:
  ```json
  {
    "title": "...",
    "content": "...",
    "section": "...",
    "source_url": "...",
    "country": "india",
    "category": "immigration"
  }
  ```
- DocumentProcessor expects this shape; if your source data differs, update `document_processor.py` accordingly

Frontend walkthrough
--------------------
- `frontend/app.py` — main streamlit runner; initializes session state (api_client, auth_manager, session_id)
- `frontend/pages/login.py` — login and signup UI (demo auth)
- `frontend/pages/country_selection.py` — country cards
- `frontend/pages/unified_chat.py` — main chat UI (voice and text), uses `utils.audio_processor.prepare_audio_for_whisper` to prepare audio for upload
- `frontend/utils/api_client.py` — API wrapper used by UI (not exhaustively documented here, but it maps to FastAPI endpoints)

Testing and local validation
----------------------------
- Several test scripts present under `backend/scripts`:
  - `test_document_processing.py`, `test_llm.py`, `test_retrieval.py`, `test_stt.py`, `test_tts.py`, etc.
- To run a single test script (example):

```powershell
python -m backend.scripts.test_retrieval
```

Note: tests may be simple scripts — not a formal pytest suite. Run them individually and inspect logs.

Operational details — logs & monitoring
--------------------------------------
- Logging configured at module level using `logging.getLogger(__name__)` and `logging.basicConfig` in `main.py`
- Start uvicorn with `--log-level debug` and `--access-log` to see request traces:

```powershell
uvicorn backend.main:app --reload --log-level debug --access-log
```

- Key log locations / messages to watch:
  - `📂 Found existing index for {country}` — retriever index found
  - `⏳ Loading FAISS index for {country}` — index loading
  - `🔨 Building FAISS index for: {COUNTRY}` — index building
  - `✅ Answer generated successfully` / LLM generation errors
  - `❌ STT processing failed` or `❌ TTS conversion failed`

Debugging common issues
-----------------------
1) ConnectionResetError / WSAECONNRESET (10054)
- Symptom: client sees a reset while calling API
- Likely causes in this project:
  - Server process crashed or got OOM during processing (index build, LLM call, TTS)
  - Long-running request exceeded proxy timeout (if behind a reverse proxy)
  - External API call (Groq) failed/closed connection unexpectedly
- How to diagnose:
  - Reproduce locally against `127.0.0.1:8000` to bypass proxies
  - Start uvicorn with debug logs and watch stdout for stack traces
  - Monitor process memory/CPU with Task Manager / `Get-Process -Name python`
  - For FAISS-heavy loads, prefer building indexes offline with `build_vector_store.py` and ensure indexes are preloaded at startup

2) Index load or OOM
- For large indices, consider using FAISS memory-mapped loading: `faiss.read_index(path, faiss.IO_FLAG_MMAP)`
- Offload index handling to a dedicated service/process if memory pressure is an issue

3) Incorrect translations or hybrid flow issues
- Currently the pipeline may translate queries before retrieval — if you want pure cross-lingual embeddings to handle queries directly, remove translator calls in `backend/routers/chat.py` before calling retriever
- If you remove translator calls, keep `translator` available for final answer translation only (if needed for user language)

Security & data privacy
-----------------------
- Sensitive keys stored in `.env`. Never commit .env to repo.
- Groq API key used for both STT and LLM — monitor usage and rotate keys as necessary
- User PII: `session_id` is stored; if user auth is added later, encrypt any PII and follow GDPR/local laws

Extensibility & where to change things (developer guide)
--------------------------------------------------------
1) Adding a new country
- Add `backend/data/laws/{new_country}.json` with expected fields
- Run `python backend/scripts/build_vector_store.py` or modify script to include new country
- Ensure `frontend/pages/country_selection.py` includes the new country card
- Add mapping in any country→language maps if required (in `text_to_speech.py`)

2) Swapping embedding model
- File: `backend/core/embeddings.py`
- Change default `model_name` parameter in `EmbeddingModel.__init__` and ensure local caching path updated
- Rebuild indices after changing embedding model

3) Removing the translation pre-step (make retrieval purely embedding-based)
- Edit `backend/routers/chat.py` — remove or bypass `translator.translate_query_to_english()` call
- Make sure `SpeechToTextHandler` return `language` if applicable, but allow retriever to accept any-language embeddings
- Update KT if you decide to keep translator for final answer translation only

4) Changing LLM
- File: `backend/core/llm_handler.py` — change `self.model`, `self.max_tokens`, `self.temperature`
- Verify Groq client supports the model name
- If switching to a different provider (OpenAI) you'll need to adapt API calls in `LLMHandler`

5) Improving search performance
- Consider approximate indices (IVF, HNSW) if datasets grow large — `faiss.IndexFlatL2` is brute-force and scales linearly with vectors
- For large indices, use `IndexIVFFlat` + `IndexIVFPQ` or HNSW implementation

Testing & CI recommendations
----------------------------
- Add a formal pytest suite with fixtures to spin up a test MongoDB instance (mongodb-memory-server or dockerized mongo)
- Add tests for:
  - `DocumentProcessor` chunking correctness
  - Embedding encode output shapes (mock model or small sample)
  - `FAISSRetriever` search correctness (small created index)
  - `LLMHandler.create_prompt()` formatting and JSON parsing (mock Groq response)
  - End-to-end smoke test: create small dataset, build index, query endpoint
- Add GitHub Actions:
  - Lint (flake8/ruff)
  - Unit tests
  - Build and smoke test steps

Deployment suggestions
----------------------
- Small production deployment (CPU-only): a VM with 8–16GB RAM (depends on index size), Python 3.11, MongoDB managed or hosted
- Run `uvicorn` behind a reverse-proxy (nginx) with proper timeouts and TLS
- For scale: separate services
  - LLM/STT calls are external (Groq) — no LLM hosting required here
  - Run a dedicated `index-serving` process if FAISS memory is high
  - Optionally, containerize with Docker and orchestrate with Kubernetes for scale

Project maintenance checklist for handover
-----------------------------------------
- [ ] Confirm `.env` values and provision Groq API key
- [ ] Verify MongoDB connectivity and indexes (run `Database.connect_db()` via startup)
- [ ] Run `python backend/scripts/build_vector_store.py` after any law updates
- [ ] Verify embedding model is present in `backend/models/e5-large` or allow first-run download
- [ ] Ensure `uvicorn` logs are observed during first runs for any exceptions

Discrepancies between KT and code (summary)
-------------------------------------------
- Translation stage: KT said translation removed — code still translates query before retrieval. Decide whether to keep translator.
- Auth: KT expected JWT backend but router is empty; frontend uses demo auth only.
- LLM: KT referenced 70b model; code uses 8b-instant.

Files & locations of key code referenced in this KT
--------------------------------------------------
- `backend/main.py` — app entry & startup
- `backend/core/embeddings.py` — embedding model
- `backend/core/retriever.py` — FAISS retriever, preload helper
- `backend/core/document_processor.py` — chunking
- `backend/core/llm_handler.py` — Groq LLM orchestration
- `backend/core/speech_to_text.py` — STT handler
- `backend/core/text_to_speech.py` — TTS handler
- `backend/core/translator.py` — translation fallback logic
- `backend/core/crud.py` — DB operations
- `backend/routers/chat.py` — main RAG router
- `backend/routers/feedback.py` — feedback endpoints
- `backend/scripts/build_vector_store.py` — offline index builder
- `backend/data/laws/*.json` — legal documents
- `backend/data/faiss_indexes/*.faiss,_metadata.pkl` — vector stores
- `frontend/app.py`, `frontend/pages/*.py` — Streamlit UI


*End of KT document*