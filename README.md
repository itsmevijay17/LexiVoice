# 📘 **LexiVoice – AI-Powered Multilingual Legal Assistant**

### *Cross-Lingual RAG • Voice Input & Output • Pure Multilingual Embeddings • FAISS • Groq LLM*

LexiVoice is a multilingual, voice-enabled, AI-powered legal assistant designed to make legal knowledge **accessible, trustworthy, and multilingual**.
Users can ask legal questions in **any language**, and LexiVoice retrieves **English legal documents** using **pure cross-lingual embeddings** (no translation layer) and delivers **citation-backed answers**, both in text and voice.

---

## 🚀 **Key Features**

* 🎙 **Voice Input** using Whisper (supports >50 languages)
* 🌍 **Multilingual Queries** — Hindi, Tamil, French, Spanish, English, and more
* 🧠 **Pure Multilingual RAG** using `intfloat/multilingual-e5-large` (NO translation anywhere)
* 🔍 **Cross-Lingual Retrieval** using FAISS cosine similarity
* 🤖 **LLM Reasoning** powered by Groq (`llama-3.1-8b-instant`)
* 🔊 **Voice Output** using gTTS in the user’s preferred language
* 📚 **Real Legal Documents** stored as structured JSON
* 📝 **Citations & Source URLs** always included
* 📊 **Query Logging & Feedback Collection** via MongoDB
* 💻 **Streamlit Frontend** with unified text + voice chat
* ⚡ **CPU-Friendly Deployment** — no GPU required

---

## 🎯 **Problem LexiVoice Solves**

Legal information is:

* complicated
* difficult for non-English speakers
* unsafe to access through hallucinating chatbots

LexiVoice solves this by providing:

* 🗣 multilingual understanding
* 🔍 accurate retrieval from real legal documents
* 📎 explainable answers with citations
* 🔊 high-quality TTS
* 💡 RAG pipeline optimized for trustworthiness

---

## 🧠 **System Architecture (Final & Correct)**

> **Pure Multilingual Embedding Pipeline — NO Google Translate, NO query/answer translation.**

```
User (Any Language: Speech/Text)
        │
        ▼
Whisper STT (if voice)
        │
        ▼
multilingual-e5-large Embedding (cross-lingual)
        │
        ▼
FAISS Vector Search (English legal documents)
        │
        ▼
Groq LLM (context-aware, citation-backed answer)
        │
        ▼
gTTS (in user-selected language)
        │
        ▼
Final Response (Text + Audio)
```

💡 *All languages are embedded into the same semantic space → cross-lingual search without translation.*

---


## 🏗 **Core Components Explained**

### **1. Embeddings — multilingual-e5-large**

* 100+ languages supported
* 384-dimensional dense embeddings
* Normalized vectors → FAISS L2 = cosine similarity
* Pure cross-lingual semantic search

### **2. Retrieval — FAISS**

Each country has its own vector index:

```
india.faiss
canada.faiss
usa.faiss
```

Search:

```
embedding(query) → FAISS → top_k chunks
```

### **3. LLM — Groq (llama-3.1-8b-instant)**

* JSON-structured output:

```json
{
  "answer": "...",
  "reasoning": "...",
  "sources": [],
  "confidence": 0.0
}
```

* Citation-obligatory prompt

### **4. STT — Whisper (via Groq)**

* Supports multilingual speech
* Converts audio → text → embeddings

### **5. TTS — gTTS**

* Produces MP3 audio in user-selected language
* Cached to avoid regeneration

### **6. Streamlit Frontend**

* Login
* Country selection
* Unified chat (text + voice)
* Real-time audio playback
* Chat history

---

Chunking strategy:

* 500 characters
* 50 character overlap
* Sentence-aligned

---

## 🛠️ **Setup Instructions**

### **1. Clone repo & create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # (Linux/Mac)
venv\Scripts\activate     # (Windows)
```

### **2. Install dependencies**

```bash
pip install -r requirements.txt
```

### **3. Create `.env`**

```
GROQ_API_KEY=your_groq_key
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=lexivoice
ENVIRONMENT=development
```

### **4. Build Vector Store (mandatory before first run)**

```bash
python backend/scripts/build_vector_store.py
```

### **5. Run backend**

```bash
uvicorn backend.main:app --reload
```

### **6. Run frontend**

```bash
cd frontend
streamlit run app.py
```

---

## 🧪 **Testing**

Run individual test utilities:

```bash
python backend/scripts/test_retrieval.py
python backend/scripts/test_stt.py
python backend/scripts/test_tts.py
python backend/scripts/test_llm.py
```

---

## 📈 **Metrics & Targets**

* Retrieval recall@k ≥ **0.70**
* End-to-end latency < **3 seconds**
* STT accuracy > **90%**
* TTS success rate **100%**
* Zero hallucination (strict citation-based generation)

---

## 🗺 **Roadmap**

### Near Term

* Add More Countries legal docs
* JWT authentication
* More countries
* Improved LLM consistency

### Long Term

* Auto-scraper for legal documents
* Conversation memory
* Fine-tuned multilingual legal LLM


## 👨‍💻 **For Developers: Extension Points**

### ➤ Add new country

1. Add `{country}.json` → `backend/data/laws`
2. Run vector store builder
3. Add country card in Streamlit

### ➤ Change embedding model

`backend/core/embeddings.py`

* Update model path & name
* Rebuild FAISS indexes

### ➤ Swap LLM model

`backend/core/llm_handler.py`

* Update `model` field
* Update token limits & temperature

---

## 📜 **License**

MIT (feel free to modify)

---

## 🤝 **Contributing**

PRs welcome!
Ensure vector stores are rebuilt before committing.

---

## ⭐ **Credits**

Built by **Vijayenth RV**
Powered by:

* Groq
* Sentence Transformers
* FAISS
* Streamlit
* gTTS
* Whisper


