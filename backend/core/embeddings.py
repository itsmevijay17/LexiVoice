# Embedding model setup
"""
Embeddings module for converting text to vectors.

Key Concept:
- Embeddings = numbers that represent text meaning
- Similar text = similar numbers
- We use sentence-transformers (free, fast, CPU-friendly)

Model: all-MiniLM-L6-v2
- Size: ~80MB (small!)
- Speed: Fast on CPU
- Quality: Good for our use case
"""
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
import logging
import os  # added for local model loading

logger = logging.getLogger(__name__)

# Local directory for storing the model (downloaded once)
# NEW: This ensures the model is only downloaded the first time.
LOCAL_MODEL_PATH = "backend/models/e5-large"


class EmbeddingModel:
    """
    Wrapper for sentence-transformer model.
    
    This model converts text into 384-dimensional vectors.
    Each dimension captures different aspects of meaning.
    """
    
    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        """
        Initialize the embedding model.
        
        Args:
            model_name: HuggingFace model identifier
                       Default: multilingual-e5-large (true multilingual semantic understanding)
        
        First run will download ~500MB model (one-time only)
        """

        # NEW LOGIC: Load from local folder if exists
        if os.path.exists(LOCAL_MODEL_PATH):
            logger.info(f"📦 Loading embedding model from local directory: {LOCAL_MODEL_PATH}")

            self.model = SentenceTransformer(
                LOCAL_MODEL_PATH,
                local_files_only=True  # Prevent re-download from HuggingFace
            )

        else:
            # First-time download (one-time only)
            logger.info(f"📥 Local model not found. Downloading model: {model_name}")
            logger.info("   (This is a one-time download ~500MB…)")

            self.model = SentenceTransformer(
                model_name,
                cache_folder=LOCAL_MODEL_PATH,   # Saves model into our project
                local_files_only=False           # Allow download this time
            )

            logger.info("✅ Model downloaded & saved locally!")

        # Get embedding dimension (384 for MiniLM / larger for e5-large)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"   Embedding dimension: {self.dimension}")
        logger.info(f"   Model ready for inference.")
    
    def encode_texts(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """
        Convert multiple texts to embeddings.
        
        Args:
            texts: List of text strings
            show_progress: Show progress bar during encoding
            
        Returns:
            numpy array of shape (len(texts), 384)
            Each row is one text's embedding
        
        Example:
            texts = ["Hello world", "Legal document"]
            embeddings = model.encode_texts(texts)
            # embeddings.shape = (2, 384)
        """
        logger.info(f"🧠 Encoding {len(texts)} texts into embeddings...")
        
        embeddings = self.model.encode(
            texts,
            batch_size=32,  # Process 32 texts at a time
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        
        logger.info(f"✅ Encoded {len(texts)} texts → {embeddings.shape}")
        return embeddings
    
    def encode_single(self, text: str) -> np.ndarray:
        """
        Convert a single text to embedding.
        
        Args:
            text: Single text string
            
        Returns:
            numpy array of shape (384,)
        
        Example:
            text = "Can I work on student visa?"
            embedding = model.encode_single(text)
            # embedding.shape = (384,)
        """
        embedding = self.model.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]
        
        return embedding
    
    def get_dimension(self) -> int:
        """Get embedding dimension (384 for MiniLM)."""
        return self.dimension


# Global model instance (lazy loading)
_embedding_model_instance = None


def get_embedding_model() -> EmbeddingModel:
    """
    Get or create the global embedding model.
    
    Why global? Loading the model is slow (~3-5 seconds).
    We load it once and reuse it everywhere.
    
    Returns:
        Singleton EmbeddingModel instance
    """
    global _embedding_model_instance
    
    if _embedding_model_instance is None:
        logger.info("🔄 Initializing global embedding model...")
        _embedding_model_instance = EmbeddingModel()
    
    return _embedding_model_instance
