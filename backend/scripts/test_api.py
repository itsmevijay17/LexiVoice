"""
Test script for complete API endpoints.

Tests:
1. Chat endpoint (POST /api/v1/chat)
2. Feedback endpoint (POST /api/v1/feedback)
3. Stats endpoint (GET /api/v1/stats)
4. Error handling

Note: Run this with the FastAPI server running!
"""
import requests
import json
import time
from typing import Dict, Any

# Base URL (make sure server is running!)
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")


def test_chat_endpoint():
    """Test the main chat endpoint."""
    print_section("TEST 1: Chat Endpoint")
    
    test_cases = [
        {
            "country": "india",
            "query": "Can I work on a student visa?",
            "session_id": "test_session_1"
        },
        {
            "country": "canada",
            "query": "How many hours can students work?",
            "session_id": "test_session_2"
        },
        {
            "country": "usa",
            "query": "What is the federal minimum wage?",
            "session_id": "test_session_3"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['country'].upper()}")
        print(f"Query: \"{test_case['query']}\"")
        print("-" * 70)
        
        try:
            # Make request
            start_time = time.time()
            response = requests.post(
                f"{API_V1}/chat/",
                json=test_case,
                headers={"Content-Type": "application/json"}
            )
            response_time = (time.time() - start_time) * 1000
            
            # Check status
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Status: {response.status_code}")
                print(f"⏱️  Response time: {response_time:.0f}ms")
                print(f"\n💬 Answer: {data['answer'][:150]}...")
                print(f"\n🧠 Reasoning: {data['reasoning'][:150]}...")
                print(f"\n📚 Sources ({len(data['sources'])}):")
                for source in data['sources'][:2]:
                    print(f"   - {source['title'][:60]}...")
                print(f"\n📊 Metadata:")
                print(f"   Query ID: {data['query_id']}")
                print(f"   Confidence: {data.get('confidence_score', 'N/A')}")
                print(f"   Country: {data['country']}")
                
                results.append({
                    'test_case': test_case,
                    'success': True,
                    'query_id': data['query_id'],
                    'response_time': response_time
                })
            else:
                print(f"❌ Error: Status {response.status_code}")
                print(f"   Detail: {response.text}")
                results.append({
                    'test_case': test_case,
                    'success': False,
                    'error': response.text
                })
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append({
                'test_case': test_case,
                'success': False,
                'error': str(e)
            })
        
        print()
    
    return results


def test_feedback_endpoint(query_ids: list):
    """Test feedback submission."""
    print_section("TEST 2: Feedback Endpoint")
    
    if not query_ids:
        print("⚠️ No query IDs available. Skipping feedback test.")
        return []
    
    test_feedbacks = [
        {
            "query_id": query_ids[0],
            "rating": 5,
            "comment": "Very helpful and accurate!"
        },
        {
            "query_id": query_ids[1] if len(query_ids) > 1 else query_ids[0],
            "rating": 4,
            "comment": "Good information, could be more detailed."
        }
    ]
    
    results = []
    
    for i, feedback in enumerate(test_feedbacks, 1):
        print(f"Feedback {i}:")
        print(f"   Query ID: {feedback['query_id']}")
        print(f"   Rating: {feedback['rating']}/5")
        print("-" * 70)
        
        try:
            response = requests.post(
                f"{API_V1}/feedback/",
                json=feedback,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"✅ Feedback submitted successfully")
                print(f"   Feedback ID: {data['id']}")
                results.append({'success': True, 'feedback_id': data['id']})
            else:
                print(f"❌ Error: Status {response.status_code}")
                print(f"   Detail: {response.text}")
                results.append({'success': False, 'error': response.text})
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append({'success': False, 'error': str(e)})
        
        print()
    
    return results


def test_stats_endpoint():
    """Test statistics endpoint."""
    print_section("TEST 3: Statistics Endpoint")
    
    try:
        response = requests.get(f"{API_V1}/stats")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Statistics retrieved successfully\n")
            print(f"📊 Query Statistics:")
            print(f"   Total queries: {data.get('total_queries', 0)}")
            
            if 'queries_by_country' in data:
                print(f"\n   Queries by country:")
                for country_stat in data['queries_by_country']:
                    print(f"      {country_stat['country']}: {country_stat['count']}")
            
            if 'feedback' in data:
                print(f"\n📝 Feedback Statistics:")
                print(f"   Total feedback: {data['feedback'].get('total_feedback', 0)}")
                print(f"   Average rating: {data['feedback'].get('average_rating', 0)}/5")
            
            return True
        else:
            print(f"❌ Error: Status {response.status_code}")
            print(f"   Detail: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_error_handling():
    """Test error handling."""
    print_section("TEST 4: Error Handling")
    
    # Test 1: Invalid country
    print("Test 4.1: Invalid country")
    try:
        response = requests.post(
            f"{API_V1}/chat/",
            json={
                "country": "invalid_country",
                "query": "test query"
            }
        )
        if response.status_code == 422:
            print("✅ Correctly rejected invalid country (422)")
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Empty query
    print("\nTest 4.2: Empty query")
    try:
        response = requests.post(
            f"{API_V1}/chat/",
            json={
                "country": "india",
                "query": ""
            }
        )
        if response.status_code == 422:
            print("✅ Correctly rejected empty query (422)")
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Invalid feedback query_id
    print("\nTest 4.3: Invalid feedback query_id")
    try:
        response = requests.post(
            f"{API_V1}/feedback/",
            json={
                "query_id": "nonexistent_id_12345",
                "rating": 5
            }
        )
        if response.status_code == 404:
            print("✅ Correctly rejected invalid query_id (404)")
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")


def main():
    """Run all API tests."""
    print(f"\n{'#'*70}")
    print(f"# LexiVoice API Test Suite")
    print(f"# Testing complete RAG pipeline via HTTP endpoints")
    print(f"# Make sure FastAPI server is running on {BASE_URL}")
    print(f"{'#'*70}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("\n❌ Server is not healthy!")
            print("   Please start the server with: python backend/main.py")
            return
    except Exception as e:
        print(f"\n❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print("\n   Please start the server with: python backend/main.py")
        return
    
    print("\n✅ Server is running and healthy!\n")
    
    # Run tests
    chat_results = test_chat_endpoint()
    
    # Extract query IDs for feedback test
    query_ids = [r['query_id'] for r in chat_results if r['success']]
    
    feedback_results = test_feedback_endpoint(query_ids)
    
    stats_success = test_stats_endpoint()
    
    test_error_handling()
    
    # Final summary
    print_section("FINAL SUMMARY")
    
    chat_success = sum(1 for r in chat_results if r['success'])
    feedback_success = sum(1 for r in feedback_results if r['success'])
    
    print(f"Chat Tests: {chat_success}/{len(chat_results)} passed")
    print(f"Feedback Tests: {feedback_success}/{len(feedback_results)} passed")
    print(f"Stats Test: {'✅ Passed' if stats_success else '❌ Failed'}")
    
    if chat_success == len(chat_results) and stats_success:
        print(f"\n🎉 All critical tests passed!")
        print(f"   Your RAG API is working perfectly!\n")
    else:
        print(f"\n⚠️ Some tests failed. Check errors above.\n")


if __name__ == "__main__":
    main()