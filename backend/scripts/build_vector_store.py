# Build FAISS index
"""
Script to build FAISS vector stores for all countries.

Run this ONCE after creating/updating legal documents.

What it does:
1. For each country (india, canada, usa)
2. Load documents → process → embed → build FAISS index
3. Save indexes to disk

After this, the indexes can be loaded instantly!
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.retriever import FAISSRetriever
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def build_all_indexes():
    """Build FAISS indexes for all supported countries."""
    countries = ['india', 'canada', 'usa']
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 Building Vector Stores for All Countries")
    logger.info(f"{'='*60}\n")
    
    results = {}
    
    for country in countries:
        try:
            # Create retriever (won't load index since it doesn't exist yet)
            retriever = FAISSRetriever(country)
            
            # Build the index
            retriever.build_index()
            
            # Get statistics
            stats = retriever.get_stats()
            results[country] = stats
            
        except Exception as e:
            logger.error(f"\n❌ Failed to build index for {country}: {e}\n")
            results[country] = {'error': str(e)}
    
    # Final summary
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 FINAL SUMMARY")
    logger.info(f"{'='*60}\n")
    
    total_vectors = 0
    for country, stats in results.items():
        if 'error' not in stats:
            logger.info(f"{country.upper()}:")
            logger.info(f"  ✅ Vectors: {stats['total_vectors']}")
            logger.info(f"  ✅ Chunks: {stats['total_chunks']}")
            logger.info(f"  ✅ Dimension: {stats['embedding_dimension']}")
            total_vectors += stats['total_vectors']
        else:
            logger.info(f"{country.upper()}:")
            logger.info(f"  ❌ Error: {stats['error']}")
        logger.info("")
    
    logger.info(f"{'='*60}")
    logger.info(f"🎉 Total vectors indexed: {total_vectors}")
    logger.info(f"{'='*60}\n")
    
    logger.info("✅ Vector stores ready for use!")
    logger.info("   Indexes saved in: backend/data/faiss_indexes/\n")


if __name__ == "__main__":
    build_all_indexes()