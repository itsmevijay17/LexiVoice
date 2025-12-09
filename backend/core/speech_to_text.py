"""
Speech-to-Text module using Groq Whisper API.

Features:
- Convert audio to text (transcription)
- Support multiple audio formats (mp3, wav, m4a, webm, etc.)
- Language detection
- High accuracy with Whisper Large V3

Why Groq Whisper?
- 100% FREE (no quotas!)
- Faster than OpenAI
- Latest model (whisper-large-v3-turbo)
- Excellent accuracy
- Same API you're already using for LLM
"""
from groq import Groq
import os
from pathlib import Path
from typing import Dict, Optional
import re
import logging
import tempfile

from backend.core.config import settings

logger = logging.getLogger(__name__)


class SpeechToTextHandler:
    """
    Handler for converting speech to text using Groq Whisper.
    
    Responsibilities:
    - Accept audio files in various formats
    - Transcribe to text using Groq Whisper API
    - Handle errors gracefully
    - Return transcription with metadata
    """
    
    # Supported audio formats (Groq Whisper supports same as OpenAI)
    SUPPORTED_FORMATS = [
        'mp3', 'mp4', 'mpeg', 'mpga', 
        'm4a', 'wav', 'webm', 'ogg', 'flac'
    ]
    
    # Max file size (25 MB - Groq limit)
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB in bytes
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize STT handler with Groq.
        
        Args:
            api_key: Groq API key (defaults to settings.GROQ_API_KEY)
        """
        self.api_key = api_key or settings.GROQ_API_KEY
        
        if not self.api_key:
            raise ValueError("Groq API key not found. Set GROQ_API_KEY in .env")
        
        # Initialize Groq client (same as LLM!)
        self.client = Groq(api_key=self.api_key)
        
        # Groq Whisper model - FREE and FAST!
        self.model = "whisper-large-v3-turbo"  # Latest & fastest model
        
        logger.info(f"🎤 STT Handler initialized (Groq Whisper)")
        logger.info(f"   Model: {self.model}")
        logger.info(f"   Provider: Groq (FREE!)")
        logger.info(f"   Supported formats: {', '.join(self.SUPPORTED_FORMATS)}")
    
    def transcribe_audio(
        self,
        audio_file,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio file to text using Groq Whisper.
        
        Args:
            audio_file: File object or file path
            language: Language code (e.g., 'en', 'hi', 'fr') - optional
            prompt: Optional text to guide transcription
            
        Returns:
            Dictionary with transcription and metadata
            
        Example:
            result = handler.transcribe_audio(audio_file)
            # Returns: {'text': '...', 'language': 'en', 'duration': 5.2}
        """
        try:
            logger.info(f"🎤 Transcribing audio with Groq Whisper...")
            
            # Step 1: Validate file
            file_info = self._validate_audio_file(audio_file)
            
            if file_info['error']:
                return {
                    'text': '',
                    'error': file_info['error'],
                    'success': False
                }
            
            logger.info(f"   File format: {file_info['format']}")
            logger.info(f"   File size: {file_info['size_mb']:.2f} MB")
            
            # Step 2: Call Groq Whisper API
            transcription = self._call_groq_whisper_api(
                audio_file,
                language=language,
                prompt=prompt
            )
            
            if not transcription:
                return {
                    'text': '',
                    'error': 'Transcription failed - empty response',
                    'success': False
                }
            
            logger.info(f"✅ Transcription successful")
            logger.info(f"   Text length: {len(transcription)} chars")
            logger.info(f"   Preview: {transcription[:100]}...")

            # Validate transcription content: ensure it's not punctuation-only or empty
            # We consider transcription valid if it contains at least one alphanumeric or script character
            # Pattern allows Latin letters, numbers, accented letters, and common unicode ranges for other scripts
            has_alpha_num = re.search(r"[A-Za-z0-9\u00C0-\u024F\u0900-\u097F]", transcription)
            if not transcription or not has_alpha_num or len(transcription.strip()) < 2:
                logger.warning("⚠️ Transcription seems to be empty or punctuation-only; marking as unsuccessful")
                return {
                    'text': transcription,
                    'language': language or 'auto-detected',
                    'file_format': file_info['format'],
                    'file_size_mb': file_info['size_mb'],
                    'success': False,
                    'error': 'Transcription was empty, very short, or punctuation-only',
                    'provider': 'groq'
                }

            return {
                'text': transcription,
                'language': language or 'auto-detected',
                'file_format': file_info['format'],
                'file_size_mb': file_info['size_mb'],
                'success': True,
                'provider': 'groq'  # NEW: Track provider
            }
            
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return {
                'text': '',
                'error': str(e),
                'success': False
            }
    
    def _validate_audio_file(self, audio_file) -> Dict:
        """
        Validate audio file format and size.
        
        Args:
            audio_file: File object or path
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Get file extension
            if hasattr(audio_file, 'filename'):
                # File upload object
                filename = audio_file.filename
                file_ext = Path(filename).suffix.lower().lstrip('.')
                
                # Get file size
                audio_file.file.seek(0, 2)  # Seek to end
                file_size = audio_file.file.tell()
                audio_file.file.seek(0)  # Reset to start
                
            elif isinstance(audio_file, str):
                # File path
                filename = audio_file
                file_ext = Path(audio_file).suffix.lower().lstrip('.')
                file_size = os.path.getsize(audio_file)
            else:
                # File object (BytesIO or similar) - try to get size and assume audio format
                try:
                    # Seek to end to get size
                    audio_file.seek(0, 2)
                    file_size = audio_file.tell()
                    audio_file.seek(0)  # Reset to start
                    
                    # Try to get filename or default to 'audio'
                    filename = getattr(audio_file, 'name', 'audio.wav')
                    file_ext = Path(filename).suffix.lower().lstrip('.')
                    
                    # If no extension, default to wav (common for streams)
                    if not file_ext:
                        file_ext = 'wav'
                        filename = 'audio.wav'
                    
                except Exception as e:
                    return {
                        'error': f'Unable to validate file object: {str(e)}',
                        'format': None,
                        'size_mb': 0
                    }
            
            # Check format
            if file_ext not in self.SUPPORTED_FORMATS:
                return {
                    'error': f'Unsupported format: {file_ext}. Supported: {", ".join(self.SUPPORTED_FORMATS)}',
                    'format': file_ext,
                    'size_mb': file_size / (1024 * 1024)
                }
            
            # Check size
            if file_size > self.MAX_FILE_SIZE:
                return {
                    'error': f'File too large: {file_size / (1024 * 1024):.2f} MB. Max: 25 MB',
                    'format': file_ext,
                    'size_mb': file_size / (1024 * 1024)
                }
            
            return {
                'error': None,
                'format': file_ext,
                'size_mb': file_size / (1024 * 1024)
            }
            
        except Exception as e:
            return {
                'error': f'File validation error: {str(e)}',
                'format': None,
                'size_mb': 0
            }
    
    def _call_groq_whisper_api(
        self,
        audio_file,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """
        Call Groq Whisper API for transcription.
        
        Args:
            audio_file: Audio file to transcribe
            language: Optional language code
            prompt: Optional prompt to guide transcription
            
        Returns:
            Transcribed text
        """
        try:
            # Need to handle file properly for Groq API
            if isinstance(audio_file, str):
                # File path - open it
                with open(audio_file, 'rb') as f:
                    file_content = f.read()
                filename = os.path.basename(audio_file)
            elif hasattr(audio_file, 'file'):
                # UploadFile object (FastAPI)
                audio_file.file.seek(0)
                file_content = audio_file.file.read()
                filename = audio_file.filename
                audio_file.file.seek(0)  # Reset for potential reuse
            elif hasattr(audio_file, 'seek'):
                # File-like object (BytesIO, etc.)
                audio_file.seek(0)
                file_content = audio_file.read()
                filename = getattr(audio_file, 'name', 'audio.wav')
                audio_file.seek(0)  # Reset for potential reuse
            else:
                # Try to read as bytes
                if isinstance(audio_file, bytes):
                    file_content = audio_file
                    filename = 'audio.wav'
                else:
                    file_content = audio_file.read()
                    filename = getattr(audio_file, 'name', 'audio.wav')
            
            # Prepare file tuple for Groq API
            # Format: (filename, file_content, content_type)
            file_tuple = (filename, file_content)
            
            # Prepare API parameters
            api_params = {
                'file': file_tuple,
                'model': self.model,
                'response_format': 'text',  # Get plain text response
            }
            
            # Add optional parameters
            if language:
                api_params['language'] = language
            
            if prompt:
                api_params['prompt'] = prompt
            
            # Call Groq Whisper API
            logger.info(f"📡 Calling Groq Whisper API...")
            transcription = self.client.audio.transcriptions.create(**api_params)
            
            # Groq returns text directly when response_format='text'
            if isinstance(transcription, str):
                result_text = transcription.strip()
            else:
                # Fallback if it returns an object
                result_text = transcription.text.strip()
            
            logger.info(f"✅ Groq Whisper API call successful")
            
            return result_text
            
        except Exception as e:
            logger.error(f"❌ Groq Whisper API call failed: {e}")
            raise
    
    def transcribe_with_fallback(
        self,
        audio_file,
        country: str = 'usa',
        user_language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe with language hinting and fallback.

        Priority for language hints:
        1. If `user_language` provided -> use that
        2. Country-specific hint (previous behavior)
        3. No hint (let model auto-detect)

        Args:
            audio_file: Audio file
            country: Country code for language hint
            user_language: Optional user preferred language (ISO 639-1)

        Returns:
            Transcription result
        """
        # Country-based language hints (legacy behavior)
        language_hints = {
            'india': 'en',      # default to English (Indian accent)
            'canada': 'en',     # English (Canadian)
            'usa': 'en'         # English (US)
        }

        # 1) Use explicit user_language if provided
        if user_language:
            language = user_language
            logger.info(f"🎤 Attempting transcription with user language hint: {language}")
            result = self.transcribe_audio(audio_file, language=language)

            # If transcription failed for explicit user_language, fall through to country hint
            if result['success']:
                return result
            logger.info(f"🔄 Transcription with user language '{language}' failed, falling back...")

        # 2) Try country-specific hint
        language = language_hints.get(country, None)
        if language:
            logger.info(f"🎤 Attempting transcription with country hint: {language} (country: {country})")
            result = self.transcribe_audio(audio_file, language=language)
            if result['success']:
                return result
            logger.info("🔄 Transcription with country hint failed, retrying without hint...")

        # 3) Final attempt without any language hint (let model auto-detect)
        result = self.transcribe_audio(audio_file, language=None)
        return result
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio formats."""
        return self.SUPPORTED_FORMATS.copy()
    
    def get_max_file_size(self) -> Dict:
        """Get maximum file size information."""
        return {
            'bytes': self.MAX_FILE_SIZE,
            'mb': self.MAX_FILE_SIZE / (1024 * 1024),
            'formatted': f"{self.MAX_FILE_SIZE / (1024 * 1024):.0f} MB"
        }
    
    def get_model_info(self) -> Dict:
        """Get information about the Whisper model being used."""
        return {
            'model': self.model,
            'provider': 'Groq',
            'cost': 'FREE',
            'speed': 'Very Fast',
            'accuracy': 'High (Whisper Large V3 Turbo)'
        }


# Global STT handler instance
_stt_handler_instance = None


def get_stt_handler() -> SpeechToTextHandler:
    """
    Get or create global STT handler instance.
    
    Returns:
        Singleton SpeechToTextHandler instance
    """
    global _stt_handler_instance
    
    if _stt_handler_instance is None:
        logger.info("🔄 Initializing global STT handler (Groq Whisper)...")
        _stt_handler_instance = SpeechToTextHandler()
    
    return _stt_handler_instance