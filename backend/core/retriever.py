# FAISS/Chroma RAG logic
"""
FAISS-based document retriever.

What it does:
1. Takes document chunks
2. Converts to embeddings
3. Stores in FAISS index
4. Searches for similar chunks when queried

Think of it like Google Search, but for legal documents!
"""
import faiss
import numpy as np
import pickle
import os
from typing import List, Dict
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

from backend.core.embeddings import get_embedding_model
from backend.core.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

# Module-level executor for background index operations
_executor = ThreadPoolExecutor(max_workers=2)




class FAISSRetriever:
    """
    FAISS-based retriever for legal documents.
    
    Flow:
    1. Build: chunks → embeddings → FAISS index → save to disk
    2. Search: query → embedding → FAISS search → return relevant chunks
    """
    
    def __init__(self, country: str):
        """
        Initialize retriever for a specific country.
        
        Args:
            country: 'india', 'canada', or 'usa'
        """
        self.country = country
        self.index = None
        self.chunks = []  # Store chunk metadata
        self.embedding_model = get_embedding_model()
        
        # Paths for saving/loading
        self.index_dir = "backend/data/faiss_indexes"
        self.index_path = f"{self.index_dir}/{country}.faiss"
        self.metadata_path = f"{self.index_dir}/{country}_metadata.pkl"
        
        # Background loading support: do not block during initialization.
        self._loading_future = None
        self._loading_lock = threading.Lock()

        # Try to load existing index asynchronously so startup isn't blocked.
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            logger.info(f"📂 Found existing index for {country}; scheduling background load")
            # Submit load to module-level executor
            try:
                _executor.submit(self.load_index)
                # Caller may inspect `self.index` or call search() which will wait briefly if needed.
            except Exception:
                # Fallback to synchronous load if executor isn't available
                logger.warning("Background executor unavailable, loading index synchronously")
                self.load_index()
        else:
            logger.info(f"🔨 No index found for {country}. Need to build first!")
    
    def build_index(self):
        """
        Build FAISS index from scratch.
        
        Steps:
        1. Load documents for this country
        2. Process into chunks
        3. Generate embeddings for all chunks
        4. Create FAISS index
        5. Save to disk
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔨 Building FAISS index for: {self.country.upper()}")
        logger.info(f"{'='*60}\n")
        
        # Step 1: Load documents
        processor = DocumentProcessor(chunk_size=500)
        documents = processor.load_documents(self.country)
        
        # Step 2: Process into chunks
        chunk_objects = processor.process_documents(documents)
        
        # Convert DocumentChunk objects to dictionaries
        self.chunks = []
        texts = []
        
        for chunk in chunk_objects:
            # Store metadata
            self.chunks.append({
                'text': chunk.text,
                'title': chunk.title,
                'section': chunk.section,
                'source_url': chunk.source_url,
                'country': chunk.country,
                'category': chunk.category,
                'chunk_id': chunk.chunk_id
            })
            texts.append(chunk.text)
        
        logger.info(f"📝 Prepared {len(texts)} text chunks")
        
        # Step 3: Generate embeddings
        logger.info(f"🧠 Generating embeddings...")
        embeddings = self.embedding_model.encode_texts(texts, show_progress=True)
        
        logger.info(f"✅ Generated embeddings: {embeddings.shape}")
        
        # Step 4: Create FAISS index
        dimension = embeddings.shape[1]  # Should be 384
        
        # IndexFlatL2 = Simple brute-force search (perfect for small datasets)
        # L2 = Euclidean distance (we normalized embeddings, so this works like cosine)
        self.index = faiss.IndexFlatL2(dimension)
        
        # Add embeddings to index
        self.index.add(embeddings.astype('float32'))
        
        logger.info(f"✅ FAISS index created with {self.index.ntotal} vectors")
        
        # Step 5: Save to disk
        self.save_index()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Index building complete for {self.country}!")
        logger.info(f"{'='*60}\n")
    
    def save_index(self):
        """
        Save FAISS index and metadata to disk.
        
        Saves 2 files:
        - .faiss file: The vector index (for fast search)
        - _metadata.pkl: The chunk information (text, title, etc.)
        """
        # Create directory if it doesn't exist
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, self.index_path)
        logger.info(f"💾 FAISS index saved: {self.index_path}")
        
        # Save metadata (chunks)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.chunks, f)
        logger.info(f"💾 Metadata saved: {self.metadata_path}")
        
        # Show file sizes
        index_size = os.path.getsize(self.index_path) / 1024  # KB
        meta_size = os.path.getsize(self.metadata_path) / 1024  # KB
        logger.info(f"📊 Index size: {index_size:.1f} KB")
        logger.info(f"📊 Metadata size: {meta_size:.1f} KB")
    
    def load_index(self):
        """
        Load FAISS index and metadata from disk.
        
        Much faster than rebuilding every time!
        """
        # Protect concurrent loads
        with self._loading_lock:
            try:
                logger.info(f"⏳ Loading FAISS index for {self.country} from {self.index_path}")
                # Load FAISS index (use faiss.read_index which may be expensive)
                self.index = faiss.read_index(self.index_path)

                # Load metadata
                with open(self.metadata_path, 'rb') as f:
                    self.chunks = pickle.load(f)

                logger.info(f"✅ Loaded index for {self.country}")
                logger.info(f"   Vectors: {self.index.ntotal}")
                logger.info(f"   Chunks: {len(self.chunks)}")

            except Exception as e:
                logger.error(f"❌ Error loading index: {e}")
                # Leave index as None so callers can decide to build or retry
                self.index = None
                self.chunks = []
                return
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search for relevant document chunks.
        
        Args:
            query: User's question (e.g., "Can I work on student visa?")
            top_k: Number of results to return (default: 3)
        
        Returns:
            List of relevant chunks with similarity scores
        
        Example:
            results = retriever.search("student visa work", top_k=3)
            # Returns top 3 most relevant chunks
        """
        # If index is not yet loaded, wait briefly for background loader to finish.
        if self.index is None:
            # If a background load is in progress give it a chance to finish
            logger.info(f"Index not ready for {self.country}; waiting briefly for load to complete")
            # Simple blocking wait loop with timeout to avoid indefinite hang
            waited = 0
            wait_step = 0.2
            max_wait = 5.0
            while self.index is None and waited < max_wait:
                threading.Event().wait(wait_step)
                waited += wait_step

            if self.index is None:
                # Still not loaded
                raise Exception(f"Index not loaded for {self.country}. Try again later or trigger build_index().")
        
        # Step 1: Convert query to embedding
        query_embedding = self.embedding_model.encode_single(query)
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        
        # Step 2: Search FAISS index
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Step 3: Retrieve chunk metadata
        results = []
        
        for distance, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                
                # Convert distance to similarity score (0-1, higher = more similar)
                # L2 distance: 0 = identical, higher = more different
                # We convert to similarity: 1/(1+distance)
                similarity = float(1 / (1 + distance))
                chunk['similarity_score'] = similarity
                
                results.append(chunk)
        
        logger.info(f"🔍 Search query: '{query}'")
        logger.info(f"   Found {len(results)} relevant chunks")
        for i, result in enumerate(results):
            logger.info(f"   {i+1}. {result['title'][:50]}... (score: {result['similarity_score']:.3f})")
        
        return results
    
    def get_stats(self) -> Dict:
        """Get statistics about the index."""
        return {
            'country': self.country,
            'total_vectors': self.index.ntotal if self.index else 0,
            'total_chunks': len(self.chunks),
            'embedding_dimension': self.embedding_model.get_dimension(),
            'index_exists': os.path.exists(self.index_path)
        }


# Global retriever cache
_retriever_cache = {}


def preload_retrievers(countries: List[str] = None):
    """
    Preload FAISS retrievers for the given list of countries.
    This schedules background loads (when index files exist) and returns the cache mapping.
    If `countries` is None, defaults to common supported countries.
    """
    if countries is None:
        countries = ["india", "canada", "usa"]

    for country in countries:
        if country not in _retriever_cache:
            logger.info(f"Preloading retriever for: {country}")
            _retriever_cache[country] = FAISSRetriever(country)

    return _retriever_cache


def get_retriever(country: str) -> FAISSRetriever:
    """
    Get or create retriever for a country.
    
    Uses caching to avoid reloading the same index multiple times.
    
    Args:
        country: 'india', 'canada', or 'usa'
        
    Returns:
        FAISSRetriever instance
    """
    if country not in _retriever_cache:
        logger.info(f"🔄 Creating retriever for {country}")
        _retriever_cache[country] = FAISSRetriever(country)
    
    return _retriever_cache[country]