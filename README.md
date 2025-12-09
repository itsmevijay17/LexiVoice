# LexiVoice – AI-Powered Multilingual Legal Assistant
# 📋 Module 2: RAG Pipeline - Simple To-Do List

---

## ✅ **Module 2.1: Prepare Legal Documents** (Day 1-2)

### **What we're doing:** Creating and organizing legal text data

#### **Tasks:**
1. ✅ Create 3 JSON files with legal documents
   - `backend/data/laws/india.json`
   - `backend/data/laws/canada.json`
   - `backend/data/laws/usa.json`

2. ✅ Create `backend/core/document_processor.py`
   - Function to load JSON files
   - Function to clean text (remove extra spaces, special characters)
   - Function to split documents into small chunks (paragraphs)

3. ✅ Create test script `backend/scripts/test_document_processing.py`
   - Test: Can we load documents?
   - Test: Are chunks the right size?
   - See statistics (how many chunks created)

**End Result:** Legal documents ready to be converted to embeddings

---

## ✅ **Module 2.2: Convert Text to Numbers (Embeddings)** (Day 3-4)

### **What we're doing:** Converting text chunks into numbers (vectors)

#### **Tasks:**
1. ✅ Create `backend/core/embeddings.py`
   - Load sentence-transformers model
   - Function: text → list of numbers (embedding)
   - Test with sample text

2. ✅ Create `backend/core/retriever.py`
   - Build FAISS index (database of vectors)
   - Function to save index to disk
   - Function to load index from disk
   - Function to search similar chunks

3. ✅ Create `backend/scripts/build_vector_store.py`
   - Run once to create FAISS indexes for all countries
   - Save indexes to `backend/data/faiss_indexes/`

**End Result:** Searchable database of legal document vectors

---

## ✅ **Module 2.3: AI Integration (LLM)** (Day 5-6)

### **What we're doing:** Connecting to Groq AI to generate answers

#### **Tasks:**
1. ✅ Create `backend/core/llm_handler.py`
   - Connect to Groq API
   - Create prompt template (how to ask AI)
   - Function: question + documents → AI answer
   - Parse AI response (extract answer, reasoning, sources)

2. ✅ Test AI responses
   - Test with sample question
   - Verify citations are included
   - Check answer quality

**End Result:** Working AI that can answer questions using documents

---

## ✅ **Module 2.4: Complete RAG Pipeline + API** (Day 7)

### **What we're doing:** Connect everything together in one API endpoint

#### **Tasks:**
1. ✅ Create `backend/routers/chat.py`
   - POST `/api/v1/chat` endpoint
   - Full flow:
     - Receive question
     - Search documents (retriever)
     - Generate answer (LLM)
     - Save to database (query log)
     - Return response

2. ✅ Update `backend/main.py`
   - Add chat router to FastAPI app

3. ✅ Test complete flow
   - Send test questions via API
   - Verify responses include answer + sources
   - Check database logs

**End Result:** Working RAG API endpoint!

---

## 📊 **Summary: 4 Simple Steps**

```
Step 2.1: Prepare Documents
   ↓
   Legal text split into small chunks
   ↓
Step 2.2: Create Embeddings
   ↓
   Chunks converted to numbers, stored in FAISS
   ↓
Step 2.3: Connect AI
   ↓
   Groq AI can generate answers from documents
   ↓
Step 2.4: Build API
   ↓
   Question → Search → AI → Answer (with sources)
```

---

## 🎯 **Let's Start with Step 2.1!**

Ready to create the legal document files? I'll give you:
- ✅ The 3 JSON files (copy-paste ready)
- ✅ Simple document processor code
- ✅ Test script to verify it works

**Should I proceed with Step 2.1 now?** 

Say "yes" and I'll give you the first set of files to create! 🚀





Features to be done:
main ui page work
faiss indexs issue
many languages isssue
