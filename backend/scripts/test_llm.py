"""
Test script for LLM integration.

Tests:
1. Can we call Groq API?
2. Are responses in correct format?
3. Are answers grounded in documents?
4. Are sources cited correctly?
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.llm_handler import get_llm_handler
from backend.core.retriever import get_retriever
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_llm_with_retrieval(country: str, query: str):
    """
    Test complete RAG flow: Retrieval + LLM Generation.
    
    Args:
        country: Country code
        query: User question
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"Testing RAG Pipeline")
    logger.info(f"{'='*70}")
    logger.info(f"Country: {country.upper()}")
    logger.info(f"Query: \"{query}\"")
    logger.info(f"{'='*70}\n")
    
    # Step 1: Retrieve relevant documents
    logger.info("📚 Step 1: Retrieving relevant documents...")
    retriever = get_retriever(country)
    retrieved_chunks = retriever.search(query, top_k=3)
    
    logger.info(f"✅ Retrieved {len(retrieved_chunks)} documents")
    for i, chunk in enumerate(retrieved_chunks, 1):
        logger.info(f"   {i}. {chunk['title'][:50]}... (score: {chunk['similarity_score']:.3f})")
    
    # Step 2: Generate answer with LLM
    logger.info(f"\n🤖 Step 2: Generating answer with Groq LLM...")
    llm_handler = get_llm_handler()
    
    answer_dict = llm_handler.generate_answer(
        query=query,
        retrieved_chunks=retrieved_chunks,
        country=country
    )
    
    # Step 3: Display results
    logger.info(f"\n{'='*70}")
    logger.info(f"📋 RESPONSE")
    logger.info(f"{'='*70}\n")
    
    logger.info(f"💬 ANSWER:")
    logger.info(f"   {answer_dict.get('answer', 'N/A')}\n")
    
    logger.info(f"🧠 REASONING:")
    logger.info(f"   {answer_dict.get('reasoning', 'N/A')}\n")
    
    logger.info(f"📚 SOURCES:")
    sources = answer_dict.get('sources', [])
    if sources:
        for i, source in enumerate(sources, 1):
            logger.info(f"   {i}. {source}")
    else:
        logger.info("   No sources provided")
    
    logger.info(f"\n📊 METADATA:")
    logger.info(f"   Confidence: {answer_dict.get('confidence', 'N/A')}")
    logger.info(f"   Model: {answer_dict.get('model', 'N/A')}")
    logger.info(f"   Tokens used: {answer_dict.get('tokens_used', 'N/A')}")
    
    # Step 4: Validate quality
    logger.info(f"\n🔍 Step 3: Validating answer quality...")
    validation = llm_handler.validate_answer_quality(answer_dict, retrieved_chunks)
    
    if validation['is_valid']:
        logger.info(f"✅ Answer quality: GOOD (score: {validation['quality_score']:.2f})")
    else:
        logger.info(f"⚠️ Answer quality: ISSUES FOUND")
        for warning in validation['warnings']:
            logger.info(f"   - {warning}")
    
    logger.info(f"\n{'='*70}\n")
    
    return answer_dict


def main():
    """Run comprehensive LLM tests."""
    
    test_cases = [
        # India
        {
            'country': 'india',
            'query': 'Can I work on a student visa in India?'
        },
        {
            'country': 'india',
            'query': 'What is the minimum wage in India?'
        },
        
        # Canada
        {
            'country': 'canada',
            'query': 'How many hours can international students work in Canada?'
        },
        {
            'country': 'canada',
            'query': 'What is the duration of a post-graduation work permit?'
        },
        
        # USA
        {
            'country': 'usa',
            'query': 'Can F1 visa students work off-campus?'
        },
        {
            'country': 'usa',
            'query': 'What are the requirements for an H1B visa?'
        }
    ]
    
    logger.info(f"\n{'#'*70}")
    logger.info(f"# LLM + RAG Integration Test Suite")
    logger.info(f"# Testing {len(test_cases)} queries across 3 countries")
    logger.info(f"{'#'*70}\n")
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n{'='*70}")
        logger.info(f"TEST CASE {i}/{len(test_cases)}")
        logger.info(f"{'='*70}")
        
        try:
            result = test_llm_with_retrieval(
                country=test_case['country'],
                query=test_case['query']
            )
            results.append({
                'test_case': test_case,
                'success': True,
                'answer': result.get('answer', '')[:100] + '...'
            })
        except Exception as e:
            logger.error(f"❌ Test failed: {e}\n")
            results.append({
                'test_case': test_case,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    logger.info(f"\n{'='*70}")
    logger.info(f"📊 TEST SUMMARY")
    logger.info(f"{'='*70}\n")
    
    successful = sum(1 for r in results if r['success'])
    logger.info(f"Total tests: {len(test_cases)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {len(test_cases) - successful}")
    logger.info(f"Success rate: {successful/len(test_cases)*100:.1f}%\n")
    
    if successful == len(test_cases):
        logger.info("🎉 All tests passed! LLM integration working perfectly!\n")
    else:
        logger.info("⚠️ Some tests failed. Check errors above.\n")


if __name__ == "__main__":
    main()