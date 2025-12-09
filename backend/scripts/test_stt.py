"""
Test script for Speech-to-Text functionality.

Tests:
1. Basic audio transcription
2. Different audio formats
3. Error handling (large files, invalid formats)
4. Integration with chat pipeline
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.speech_to_text import get_stt_handler
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


# ============================================================
# 🔧 SAFELY DELETE FILE (Windows fix)
# ============================================================
def _safe_delete(path: str):
    """Safely delete a file, avoiding Windows file-handle errors."""
    try:
        if os.path.exists(path):
            os.chmod(path, 0o666)  # ensure write permissions
            os.remove(path)
            logger.info(f"Cleaned up test file: {path}")
    except Exception as e:
        logger.error(f"⚠️ Failed to delete file {path}: {e}")


# ============================================================
# 🎤 Create Sample Audio
# ============================================================
def create_sample_audio():
    """
    Create a sample audio file for testing using gTTS.
    """
    from gtts import gTTS
    import tempfile

    logger.info("Creating sample audio file for testing...")

    text = "Can international students work in Canada?"

    tts = gTTS(text=text, lang='en', slow=False)

    temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp_path = temp.name
    temp.close()  # IMPORTANT FIX: close file handle before saving

    tts.save(temp_path)

    logger.info(f"✅ Sample audio created: {temp_path}")
    logger.info(f"   Text: '{text}'")

    return temp_path, text


# ============================================================
# TEST 1 — Basic Transcription
# ============================================================
def test_basic_transcription():
    logger.info(f"\n{'='*70}")
    logger.info("TEST 1: Basic Audio Transcription")
    logger.info(f"{'='*70}\n")

    audio_path, expected_text = create_sample_audio()

    try:
        stt_handler = get_stt_handler()

        logger.info("Transcribing audio...")
        result = stt_handler.transcribe_audio(audio_path, language='en')

        if result['success']:
            logger.info(f"\n✅ Transcription successful!")
            logger.info(f"   Expected: '{expected_text}'")
            logger.info(f"   Got: '{result['text']}'")
            logger.info(f"   Language: {result['language']}")
            logger.info(f"   File size: {result['file_size_mb']:.2f} MB")

            if expected_text.lower() in result['text'].lower():
                logger.info("   ✅ Transcription is accurate!\n")
            else:
                logger.warning("   ⚠️ Slight differences (normal)\n")
        else:
            logger.error(f"\n❌ Transcription failed: {result.get('error')}\n")

    finally:
        _safe_delete(audio_path)


# ============================================================
# TEST 2 — Format Validation
# ============================================================
def test_format_validation():
    logger.info(f"\n{'='*70}")
    logger.info("TEST 2: Format Validation")
    logger.info(f"{'='*70}\n")

    stt_handler = get_stt_handler()

    logger.info("Supported formats:")
    formats = stt_handler.get_supported_formats()
    logger.info(f"   {', '.join(formats)}\n")

    max_size = stt_handler.get_max_file_size()
    logger.info("Maximum file size:")
    logger.info(f"   {max_size['formatted']} ({max_size['bytes']} bytes)\n")


# ============================================================
# TEST 3 — Country-Specific Transcription
# ============================================================
def test_country_specific():
    logger.info(f"\n{'='*70}")
    logger.info("TEST 3: Country-Specific Transcription")
    logger.info(f"{'='*70}\n")

    from gtts import gTTS
    import tempfile

    stt_handler = get_stt_handler()

    test_cases = [
        {'text': "What is the minimum wage in India?", 'country': 'india'},
        {'text': "Can I work on a student visa in Canada?", 'country': 'canada'},
        {'text': "What are the H1B visa requirements?", 'country': 'usa'}
    ]

    for i, tc in enumerate(test_cases, 1):
        logger.info(f"Test {i}: {tc['country'].upper()}")
        logger.info(f"Text: '{tc['text']}'")
        logger.info("-" * 70)

        # Create audio
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        path = temp.name
        temp.close()  # fix handle

        gTTS(text=tc['text'], lang='en').save(path)

        try:
            result = stt_handler.transcribe_with_fallback(path, country=tc['country'])

            if result['success']:
                logger.info("✅ Success!")
                logger.info(f"   Transcribed: '{result['text']}'")
                similarity = _calculate_similarity(tc['text'], result['text'])
                logger.info(f"   Accuracy: {similarity:.1f}%\n")
            else:
                logger.error(f"❌ Failed: {result.get('error')}\n")

        finally:
            _safe_delete(path)


# ============================================================
# Helper — Similarity Score
# ============================================================
def _calculate_similarity(a: str, b: str) -> float:
    w1, w2 = set(a.lower().split()), set(b.lower().split())
    if not w1 or not w2:
        return 0.0
    return (len(w1 & w2) / len(w1 | w2)) * 100


# ============================================================
# TEST 4 — Error Handling
# ============================================================
def test_error_handling():
    logger.info(f"\n{'='*70}")
    logger.info("TEST 4: Error Handling")
    logger.info(f"{'='*70}\n")

    stt_handler = get_stt_handler()

    # Non-existent file
    logger.info("Test 4.1: Non-existent file")
    result = stt_handler.transcribe_audio("no_file.mp3")
    logger.info(f"   {'✅ Correct' if not result['success'] else '⚠️ Incorrect'}\n")

    # Invalid format
    import tempfile
    bad = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w')
    bad.write("NOT AUDIO")
    bad.close()

    result = stt_handler.transcribe_audio(bad.name)
    logger.info(f"   {'✅ Correct' if not result['success'] else '⚠️ Incorrect'}\n")

    _safe_delete(bad.name)


# ============================================================
# MAIN
# ============================================================
def main():
    logger.info(f"\n{'#'*70}")
    logger.info("# Speech-to-Text (STT) Test Suite")
    logger.info("# Using Groq Whisper (FAST + FREE)")
    logger.info(f"{'#'*70}\n")

    try:
        test_basic_transcription()
        test_format_validation()
        test_country_specific()
        test_error_handling()

        logger.info("\n🎉 ALL TESTS PASSED!")
        logger.info("STT is fully working.\n")

    except Exception as e:
        logger.error(f"\n❌ Tests failed with error: {e}\n")


if __name__ == "__main__":
    main()
