import os

# Define folder structure
folders = [
    "frontend/components",
    "frontend/assets",
    "frontend/utils",
    "backend/routers",
    "backend/core",
    "backend/data/laws",
    "backend/data/faiss_indexes",
    "backend/scripts",
    "backend/tests",
]

# Define placeholder files with minimal content
files = {
    "frontend/app.py": "# Streamlit entry point\n",
    "frontend/components/chat_ui.py": "# Chat UI component\n",
    "frontend/components/country_selector.py": "# Country selection component\n",
    "frontend/components/voice_input.py": "# Voice input component\n",
    "frontend/utils/api_client.py": "# API client utilities\n",
    "frontend/utils/audio_utils.py": "# Audio processing helpers\n",

    "backend/main.py": "# FastAPI entry point\n",
    "backend/routers/chat.py": "# Chat route handler\n",
    "backend/routers/auth.py": "# Auth route handler\n",
    "backend/routers/feedback.py": "# Feedback route handler\n",
    "backend/core/config.py": "# Environment and config\n",
    "backend/core/database.py": "# MongoDB connection\n",
    "backend/core/embeddings.py": "# Embedding model setup\n",
    "backend/core/retriever.py": "# FAISS/Chroma RAG logic\n",
    "backend/core/llm_handler.py": "# Groq or fallback LLM handler\n",
    "backend/core/speech_to_text.py": "# Whisper API integration\n",
    "backend/core/translator.py": "# Google Translate wrapper\n",
    "backend/core/utils.py": "# Misc helper functions\n",
    "backend/scripts/scrape_laws.py": "# Scraper for legal documents\n",
    "backend/scripts/build_vector_store.py": "# Build FAISS index\n",
    "backend/tests/test_rag_pipeline.py": "# Unit tests for RAG pipeline\n",
    "backend/tests/test_api_endpoints.py": "# API endpoint tests\n",
    "backend/requirements.txt": "# List of dependencies\n",
    ".env.example": "MONGODB_URI=\nOPENAI_API_KEY=\nGROQ_API_KEY=\nGOOGLE_TRANSLATE_API_KEY=\n",
    "README.md": "# LexiVoice – AI-Powered Multilingual Legal Assistant\n",
    "LICENSE": "MIT License\n",
    "setup_instructions.md": "# Setup Instructions\n\n1. Fill .env\n2. Install dependencies\n3. Run backend + frontend\n"
}

# Create folders
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Create placeholder files
for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ LexiVoice project structure created successfully!")
