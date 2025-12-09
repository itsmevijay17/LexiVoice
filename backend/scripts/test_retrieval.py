"""
Test script for retrieval system.

Tests:
1. Can we load the indexes?
2. Can we search for relevant documents?
3. Are results actually relevant?
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.retriever import get_retriever
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_retrieval(country: str, queries: list):
    """Test retrieval for a country with sample queries."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {country.upper()}")
    logger.info(f"{'='*60}\n")
    
    # Get retriever
    retriever = get_retriever(country)
    
    # Test each query
    for query in queries:
        logger.info(f"\n📝 Query: \"{query}\"")
        logger.info(f"-" * 60)
        
        # Search
        results = retriever.search(query, top_k=3)
        
        # Display results
        for i, result in enumerate(results, 1):
            logger.info(f"\n   Result {i} (Score: {result['similarity_score']:.3f}):")
            logger.info(f"   Title: {result['title']}")
            logger.info(f"   Section: {result['section']}")
            logger.info(f"   Category: {result['category']}")
            logger.info(f"   Text: {result['text'][:200]}...")


def main():
    """Test retrieval for all countries."""
    
    test_cases = {
        'india': [
            "Can I work on a student visa?",
            "What is the minimum wage?",
            "Can I return a defective product?"
        ],
        'canada': [
            "How many hours can international students work?",
            "What is the federal minimum wage in Canada?",
            "Post graduation work permit duration"
        ],
        'usa': [
            "F1 visa work restrictions",
            "H1B visa requirements",
            "Federal minimum wage rate"
        ]
    }
    
    for country, queries in test_cases.items():
        try:
            test_retrieval(country, queries)
        except Exception as e:
            logger.error(f"\n❌ Error testing {country}: {e}\n")
    
    logger.info(f"\n{'='*60}")
    logger.info("✅ Retrieval testing complete!")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    main()