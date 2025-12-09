"""
Text-to-Speech module using gTTS.

Features:
- Convert text responses to audio
- Support multiple languages
- Cache audio files for efficiency
- Return audio file paths or base64

Why gTTS?
- Free (no API keys needed)
- Supports 100+ languages
- Good quality
- Easy to use
"""
from gtts import gTTS
import os
import base64
from pathlib import Path
from typing import Optional, Dict
import hashlib
import logging

logger = logging.getLogger(__name__)


class TextToSpeechHandler:
    """
    Handler for converting text to speech using gTTS.
    
    Features:
    - Converts text to MP3 audio
    - Caches audio files (avoid regenerating same text)
    - Returns file path or base64 encoded audio
    """
    
    def __init__(self, audio_dir: str = "backend/data/audio"):
        """
        Initialize TTS handler.
        
        Args:
            audio_dir: Directory to store audio files
        """
        self.audio_dir = audio_dir
        
        # Create audio directory if it doesn't exist
        os.makedirs(audio_dir, exist_ok=True)
        
        # Language mapping (ISO 639-1 code → gTTS language code)
        # gTTS supports 100+ languages
        self.language_map = {
            'en': 'en',         # English
            'hi': 'hi',         # Hindi
            'es': 'es',         # Spanish
            'fr': 'fr',         # French
            'de': 'de',         # German
            'zh': 'zh-CN',      # Chinese (Simplified)
            'ja': 'ja',         # Japanese
            'ko': 'ko',         # Korean
            'pt': 'pt',         # Portuguese
            'ru': 'ru',         # Russian
            'it': 'it',         # Italian
            'nl': 'nl',         # Dutch
            'sv': 'sv',         # Swedish
            'pl': 'pl',         # Polish
            'tr': 'tr',         # Turkish
            'ar': 'ar',         # Arabic
            'te': 'te',         # Telugu
            'ta': 'ta',         # Tamil
            'bn': 'bn',         # Bengali
        }
        
        # Legacy country → language mapping (for backwards compatibility)
        self.country_language_map = {
            'india': 'en',      # English (Indian accent available)
            'canada': 'en',     # English (Canadian accent)
            'usa': 'en'         # English (US accent)
        }
        
        logger.info(f"🔊 TTS Handler initialized")
        logger.info(f"   Audio directory: {audio_dir}")
        logger.info(f"   Supported languages: {len(self.language_map)}")
    
    def text_to_speech(
        self, 
        text: str, 
        country: str = 'usa',
        language: str = 'en',
        return_format: str = 'path'
    ) -> Dict:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert
            country: Country for legacy support (deprecated, use language)
            language: Language code (ISO 639-1, e.g., 'en', 'hi', 'es')
            return_format: 'path' or 'base64'
            
        Returns:
            Dictionary with audio info (path or base64 data)
        """
        try:
            logger.info(f"🔊 Converting text to speech...")
            logger.info(f"   Text length: {len(text)} chars")
            logger.info(f"   Language: {language}")
            logger.info(f"   Country: {country}")
            
            # Determine language code
            lang_code = self._get_language_code(language, country)
            
            # Step 1: Check cache (avoid regenerating same audio)
            audio_path = self._get_cached_audio(text, language, country)
            
            if audio_path and os.path.exists(audio_path):
                logger.info(f"✅ Using cached audio: {audio_path}")
            else:
                # Step 2: Generate new audio
                audio_path = self._generate_audio(text, lang_code, language, country)
                logger.info(f"✅ Generated new audio: {audio_path}")
            
            # Step 3: Return in requested format
            if return_format == 'base64':
                audio_data = self._audio_to_base64(audio_path)
                return {
                    'audio_base64': audio_data,
                    'format': 'mp3',
                    'cached': os.path.exists(audio_path),
                    'language': language
                }
            else:
                return {
                    'audio_path': audio_path,
                    'format': 'mp3',
                    'cached': os.path.exists(audio_path),
                    'language': language
                }
                
        except Exception as e:
            logger.error(f"❌ TTS conversion failed: {e}")
            return {
                'error': str(e),
                'audio_path': None,
                'audio_base64': None
            }
    
    def _generate_audio(self, text: str, lang_code: str, language: str, country: str) -> str:
        """
        Generate audio file from text.
        
        Args:
            text: Text to convert
            lang_code: gTTS language code
            language: ISO 639-1 language code
            country: Country code
            
        Returns:
            Path to generated audio file
        """
        # Limit text length (gTTS has limits)
        max_chars = 5000  # gTTS limit is ~5000 chars
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            logger.warning(f"⚠️ Text truncated to {max_chars} chars")
        
        # Generate unique filename based on language, country, and text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        filename = f"{language}_{country}_{text_hash}.mp3"
        audio_path = os.path.join(self.audio_dir, filename)
        
        # Generate audio with gTTS
        logger.info(f"   Using gTTS language code: {lang_code}")
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(audio_path)
        
        # Get file size for logging
        file_size = os.path.getsize(audio_path) / 1024  # KB
        logger.info(f"   Audio file size: {file_size:.1f} KB")
        
        return audio_path
    
    def _get_language_code(self, language: str, country: str) -> str:
        """
        Get gTTS language code from language or country.
        
        Args:
            language: ISO 639-1 language code (preferred)
            country: Country code (fallback)
            
        Returns:
            gTTS compatible language code
        """
        # Try language code first
        if language and language in self.language_map:
            return self.language_map[language]
        
        # Fall back to country
        if country and country in self.country_language_map:
            return self.country_language_map[country]
        
        # Default to English
        logger.warning(f"⚠️ Language '{language}' or country '{country}' not supported, using English")
        return 'en'
    
    def _get_cached_audio(self, text: str, language: str, country: str) -> Optional[str]:
        """
        Check if audio file already exists in cache.
        
        Args:
            text: Text to check
            language: Language code
            country: Country code
            
        Returns:
            Path to cached audio if exists, None otherwise
        """
        text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        filename = f"{language}_{country}_{text_hash}.mp3"
        audio_path = os.path.join(self.audio_dir, filename)
        
        if os.path.exists(audio_path):
            return audio_path
        return None
    
    def _audio_to_base64(self, audio_path: str) -> str:
        """
        Convert audio file to base64 string.
        
        Useful for API responses (embed audio in JSON).
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Base64 encoded audio string
        """
        with open(audio_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return audio_base64
    
    def convert_answer_to_audio(
        self, 
        answer_text: str, 
        country: str,
        language: str = 'en',
        include_reasoning: bool = False,
        reasoning_text: str = ""
    ) -> Dict:
        """
        Convert chat answer to audio.
        
        Optionally includes reasoning for complete audio response.
        
        Args:
            answer_text: Main answer text
            country: Country code
            language: Language code (ISO 639-1, e.g., 'en', 'hi', 'es')
            include_reasoning: Whether to include reasoning
            reasoning_text: Reasoning text
            
        Returns:
            Audio info dictionary
        """
        # Combine text if needed
        if include_reasoning and reasoning_text:
            full_text = f"{answer_text}. {reasoning_text}"
        else:
            full_text = answer_text
        
        # Clean text for speech (remove special characters)
        full_text = self._clean_text_for_speech(full_text)
        
        # Generate audio
        return self.text_to_speech(full_text, country=country, language=language, return_format='base64')
    
    def _clean_text_for_speech(self, text: str) -> str:
        """
        Clean text for better speech output.
        
        Removes:
        - Markdown formatting
        - Special characters
        - URLs (reads them as text)
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        import re
        
        # Remove markdown bold/italics
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        
        # Remove URLs (or replace with "link")
        text = re.sub(r'http[s]?://\S+', 'link', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get list of supported languages.
        
        Returns:
            Dictionary of ISO 639-1 codes → language names with gTTS codes
        """
        return self.language_map.copy()
    
    def clear_cache(self, older_than_days: int = 7) -> int:
        """
        Clear old cached audio files.
        
        Args:
            older_than_days: Remove files older than this many days
            
        Returns:
            Number of files removed
        """
        import time
        
        removed_count = 0
        current_time = time.time()
        
        for filename in os.listdir(self.audio_dir):
            file_path = os.path.join(self.audio_dir, filename)
            
            if os.path.isfile(file_path):
                file_age_days = (current_time - os.path.getmtime(file_path)) / 86400
                
                if file_age_days > older_than_days:
                    os.remove(file_path)
                    removed_count += 1
        
        logger.info(f"🗑️ Cleared {removed_count} cached audio files older than {older_than_days} days")
        return removed_count


# Global TTS handler instance
_tts_handler_instance = None


def get_tts_handler() -> TextToSpeechHandler:
    """
    Get or create global TTS handler instance.
    
    Returns:
        Singleton TextToSpeechHandler instance
    """
    global _tts_handler_instance
    
    if _tts_handler_instance is None:
        logger.info("🔄 Initializing global TTS handler...")
        _tts_handler_instance = TextToSpeechHandler()
    
    return _tts_handler_instance