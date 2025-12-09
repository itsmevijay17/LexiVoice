# API client utilities
"""
API client for communicating with LexiVoice backend.

Handles all HTTP requests to backend endpoints.
"""
import requests
import base64
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class LexiVoiceAPI:
    """
    API client for LexiVoice backend.
    
    Handles:
    - Text chat requests
    - Voice chat requests
    - Feedback submission
    - Statistics retrieval
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize API client.
        
        Args:
            base_url: Backend API base URL
        """
        self.base_url = base_url
        self.api_v1 = f"{base_url}/api/v1"
        
    def health_check(self) -> Dict:
        """
        Check if backend is healthy.
        
        Returns:
            Health status dictionary
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def chat_text(
        self,
        country: str,
        query: str,
        session_id: Optional[str] = None,
        include_audio: bool = False,
        user_language: str = 'en'
    ) -> Dict:
        """
        Send text chat request.
        
        Args:
            country: Country code (india/canada/usa)
            query: User's question
            session_id: Optional session ID
            include_audio: Whether to include TTS audio
            user_language: User's preferred language (ISO 639-1 code)
            
        Returns:
            Chat response dictionary
        """
        try:
            payload = {
                "country": country,
                "query": query,
                "session_id": session_id,
                "include_audio": include_audio,
                "user_language": user_language
            }
            
            response = requests.post(
                f"{self.api_v1}/chat/",
                json=payload,
                timeout=30  # 30 seconds timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            return {"error": "Request timeout. Please try again."}
        except requests.exceptions.RequestException as e:
            logger.error(f"Chat request failed: {e}")
            return {"error": f"Request failed: {str(e)}"}
    
    def chat_voice(
        self,
        audio_bytes: bytes,
        country: str,
        session_id: Optional[str] = None,
        include_audio: bool = True,
        user_language: str = 'en'
    ) -> Dict:
        """
        Send voice chat request.
        
        Args:
            audio_bytes: Audio file bytes
            country: Country code
            session_id: Optional session ID
            include_audio: Whether to include audio response
            user_language: User's preferred language (ISO 639-1 code)
            
        Returns:
            Chat response dictionary
        """
        try:
            # Prepare multipart form data
            files = {
                'audio_file': ('recording.wav', audio_bytes, 'audio/wav')
            }
            
            data = {
                'country': country,
                'session_id': session_id or '',
                'include_audio': str(include_audio).lower(),
                'user_language': user_language
            }
            
            response = requests.post(
                f"{self.api_v1}/chat/voice",
                files=files,
                data=data,
                timeout=60  # Voice processing takes longer
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            return {"error": "Voice processing timeout. Please try again."}
        except requests.exceptions.RequestException as e:
            logger.error(f"Voice chat failed: {e}")
            return {"error": f"Request failed: {str(e)}"}
    
    def submit_feedback(
        self,
        query_id: str,
        rating: int,
        comment: Optional[str] = None
    ) -> Dict:
        """
        Submit feedback for a query.
        
        Args:
            query_id: Query ID
            rating: Rating (1-5)
            comment: Optional comment
            
        Returns:
            Feedback response
        """
        try:
            payload = {
                "query_id": query_id,
                "rating": rating,
                "comment": comment
            }
            
            response = requests.post(
                f"{self.api_v1}/feedback/",
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Feedback submission failed: {e}")
            return {"error": str(e)}
    
    def get_stats(self) -> Dict:
        """
        Get system statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            response = requests.get(f"{self.api_v1}/stats", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Stats retrieval failed: {e}")
            return {"error": str(e)}
    
    def decode_audio(self, audio_base64: str) -> bytes:
        """
        Decode base64 audio to bytes.
        
        Args:
            audio_base64: Base64 encoded audio
            
        Returns:
            Audio bytes
        """
        try:
            return base64.b64decode(audio_base64)
        except Exception as e:
            logger.error(f"Audio decoding failed: {e}")
            return b""