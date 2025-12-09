"""
Test script for document processing.

What it does:
1. Load documents for each country
2. Process them into chunks
3. Show statistics
4. Display sample chunks

Run this to verify Step 2.1 is working!
"""
import sys
import os

# Add backend to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.document_processor import DocumentProcessor
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_single_country(country: str):
    """Test document processing for one country."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {country.upper()}")
    logger.info(f"{'='*60}\n")
    
    # Create processor
    processor = DocumentProcessor(chunk_size=500)
    
    # Load documents
    documents = processor.load_documents(country)
    logger.info(f"📥 Loaded {len(documents)} documents\n")
    
    # Process into chunks
    chunks = processor.process_documents(documents)
    
    # Get statistics
    stats = processor.get_statistics(chunks)
    
    # Display stats
    logger.info(f"📊 Statistics:")
    logger.info(f"   Total chunks created: {stats['total_chunks']}")
    logger.info(f"   Average chunk length: {stats['avg_chunk_length']:.0f} characters")
    logger.info(f"   Shortest chunk: {stats['min_chunk_length']} characters")
    logger.info(f"   Longest chunk: {stats['max_chunk_length']} characters")
    
    # Show category breakdown
    logger.info(f"\n📂 Chunks by category:")
    for category, count in stats['chunks_by_category'].items():
        logger.info(f"   {category}: {count} chunks")
    
    # Show sample chunks
    logger.info(f"\n📝 Sample chunks:\n")
    for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
        logger.info(f"   --- Chunk {i+1} ---")
        logger.info(f"   Title: {chunk.title}")
        logger.info(f"   Section: {chunk.section}")
        logger.info(f"   Category: {chunk.category}")
        logger.info(f"   Length: {len(chunk.text)} characters")
        logger.info(f"   Text preview: {chunk.text[:150]}...")
        logger.info("")
    
    return stats


def main():
    """Test all countries and show summary."""
    countries = ['india', 'canada', 'usa']
    all_stats = {}
    
    for country in countries:
        try:
            stats = test_single_country(country)
            all_stats[country] = stats
        except Exception as e:
            logger.error(f"❌ Error processing {country}: {e}")
    
    # Overall summary
    logger.info(f"\n{'='*60}")
    logger.info(f"📈 OVERALL SUMMARY")
    logger.info(f"{'='*60}\n")
    
    total_chunks = sum(s['total_chunks'] for s in all_stats.values())
    total_docs = sum(s['total_documents'] for s in all_stats.values())
    
    logger.info(f"Total documents: {total_docs}")
    logger.info(f"Total chunks: {total_chunks}")
    logger.info(f"Average chunks per document: {total_chunks/total_docs:.1f}")
    
    logger.info(f"\nBreakdown by country:")
    for country, stats in all_stats.items():
        logger.info(f"  {country}: {stats['total_chunks']} chunks from {stats['total_documents']} documents")
    
    # Save results
    os.makedirs('backend/data', exist_ok=True)
    with open('backend/data/processing_stats.json', 'w') as f:
        json.dump(all_stats, f, indent=2)
    
    logger.info(f"\n💾 Statistics saved to: backend/data/processing_stats.json")
    logger.info(f"\n✅ Step 2.1 Complete! Ready for Step 2.2 (Embeddings)\n")


if __name__ == "__main__":
    main()