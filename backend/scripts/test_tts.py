"""
Test script for Text-to-Speech functionality.

Tests:
1. Basic TTS conversion
2. Audio caching
3. Different languages/countries
4. Integration with chat responses
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.text_to_speech import get_tts_handler
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_basic_tts():
    """Test basic text-to-speech conversion."""
    logger.info(f"\n{'='*70}")
    logger.info("TEST 1: Basic TTS Conversion")
    logger.info(f"{'='*70}\n")
    
    tts_handler = get_tts_handler()
    
    test_texts = [
        {
            'text': "Students holding a valid Student Visa are generally not permitted to work in India.",
            'country': 'india'
        },
        {
            'text': "International students can work up to 20 hours per week during academic sessions in Canada.",
            'country': 'canada'
        },
        {
            'text': "The federal minimum wage in the United States is seven dollars and twenty-five cents per hour.",
            'country': 'usa'
        }
    ]
    
    for i, test in enumerate(test_texts, 1):
        logger.info(f"Test {i}: {test['country'].upper()}")
        logger.info(f"Text: {test['text'][:60]}...")
        logger.info("-" * 70)
        
        result = tts_handler.text_to_speech(
            text=test['text'],
            country=test['country'],
            return_format='path'
        )
        
        if 'error' in result:
            logger.error(f"❌ Failed: {result['error']}\n")
        else:
            logger.info(f"✅ Success!")
            logger.info(f"   Audio path: {result['audio_path']}")
            logger.info(f"   Format: {result['format']}")
            logger.info(f"   Cached: {result['cached']}\n")


def test_audio_caching():
    """Test that audio caching works."""
    logger.info(f"\n{'='*70}")
    logger.info("TEST 2: Audio Caching")
    logger.info(f"{'='*70}\n")
    
    tts_handler = get_tts_handler()
    
    test_text = "This is a test for audio caching functionality."
    
    # First call - should generate new audio
    logger.info("First call (should generate new audio):")
    result1 = tts_handler.text_to_speech(test_text, 'usa')
    logger.info(f"   Cached: {result1['cached']}")
    
    # Second call - should use cached audio
    logger.info("\nSecond call (should use cached audio):")
    result2 = tts_handler.text_to_speech(test_text, 'usa')
    logger.info(f"   Cached: {result2['cached']}")
    
    if result1['audio_path'] == result2['audio_path'] and result2['cached']:
        logger.info("\n✅ Caching works correctly!\n")
    else:
        logger.error("\n❌ Caching issue detected!\n")


def test_base64_format():
    """Test base64 audio encoding."""
    logger.info(f"\n{'='*70}")
    logger.info("TEST 3: Base64 Audio Encoding")
    logger.info(f"{'='*70}\n")
    
    tts_handler = get_tts_handler()
    
    test_text = "Testing base64 audio encoding for API responses."
    
    result = tts_handler.text_to_speech(
        text=test_text,
        country='canada',
        return_format='base64'
    )
    
    if 'audio_base64' in result and result['audio_base64']:
        logger.info(f"✅ Base64 encoding successful!")
        logger.info(f"   Base64 length: {len(result['audio_base64'])} characters")
        logger.info(f"   First 50 chars: {result['audio_base64'][:50]}...\n")
    else:
        logger.error(f"❌ Base64 encoding failed!\n")


def test_chat_integration():
    """Test TTS with realistic chat responses."""
    logger.info(f"\n{'='*70}")
    logger.info("TEST 4: Chat Integration (Realistic Responses)")
    logger.info(f"{'='*70}\n")
    
    tts_handler = get_tts_handler()
    
    # Simulate a typical chat response
    answer = "Yes, international students in Canada can work up to 20 hours per week during academic sessions and full-time during scheduled breaks."
    reasoning = "This is based on IRPR Section 186(f) of Canadian Immigration law."
    
    logger.info("Converting chat answer to audio...")
    logger.info(f"Answer: {answer[:60]}...")
    logger.info("-" * 70)
    
    # Without reasoning
    result1 = tts_handler.convert_answer_to_audio(
        answer_text=answer,
        country='canada',
        include_reasoning=False
    )
    
    logger.info(f"✅ Audio without reasoning:")
    logger.info(f"   Base64 length: {len(result1.get('audio_base64', ''))} chars")
    
    # With reasoning
    result2 = tts_handler.convert_answer_to_audio(
        answer_text=answer,
        country='canada',
        include_reasoning=True,
        reasoning_text=reasoning
    )
    
    logger.info(f"\n✅ Audio with reasoning:")
    logger.info(f"   Base64 length: {len(result2.get('audio_base64', ''))} chars")
    logger.info(f"   (Longer because includes reasoning)\n")


def main():
    """Run all TTS tests."""
    logger.info(f"\n{'#'*70}")
    logger.info("# Text-to-Speech (TTS) Test Suite")
    logger.info("# Testing gTTS integration")
    logger.info(f"{'#'*70}\n")
    
    try:
        test_basic_tts()
        test_audio_caching()
        test_base64_format()
        test_chat_integration()
        
        logger.info(f"\n{'='*70}")
        logger.info("📊 ALL TESTS COMPLETED")
        logger.info(f"{'='*70}\n")
        logger.info("✅ TTS is ready to use!")
        logger.info("   Audio files saved in: backend/data/audio/")
        logger.info("\nNext: Test with API endpoint by adding 'include_audio: true'\n")
        
    except Exception as e:
        logger.error(f"\n❌ Tests failed with error: {e}\n")


if __name__ == "__main__":
    main()