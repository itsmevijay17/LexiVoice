"""
Pydantic models for request/response validation (MVP - No Auth).
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CountryEnum(str, Enum):
    """Supported countries."""
    INDIA = "india"
    CANADA = "canada"
    USA = "usa"


# ============= Chat Schemas =============
class ChatRequest(BaseModel):
    """Chat query request."""
    country: CountryEnum
    query: str = Field(..., min_length=5, max_length=1000)
    user_language: str = Field(
        default="en",
        description="User's preferred language (ISO 639-1 code)"
    )
    session_id: Optional[str] = None  # For tracking conversations
    include_audio: bool = Field(
        default=False,
        description="Whether to generate and return TTS audio"
    )  # ← NEW


class SourceDocument(BaseModel):
    """Legal source document reference."""
    title: str
    section: Optional[str] = None
    url: Optional[str] = None
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Chat query response with explainability."""
    query_id: str
    answer: str
    reasoning: str
    sources: List[SourceDocument]
    country: str
    user_language: str = Field(
        default="en",
        description="User's preferred language (ISO 639-1 code)"
    )
    timestamp: datetime
    confidence_score: Optional[float] = None
    audio_base64: Optional[str] = Field(
        default=None,
        description="Base64 encoded audio (if include_audio=True)"
    )  # ← NEW
    audio_format: Optional[str] = Field(
        default=None,
        description="Audio format (e.g., mp3)"
    )  # ← NEW


# ============= Feedback Schemas =============
class FeedbackCreate(BaseModel):
    """Feedback submission request."""
    query_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)


class FeedbackResponse(BaseModel):
    """Feedback response."""
    id: str
    query_id: str
    rating: int
    comment: Optional[str]
    created_at: datetime


# ============= Database Models =============
class QueryLogDB(BaseModel):
    """Query log model for MongoDB."""
    session_id: Optional[str] = None
    country: str
    user_language: str = Field(
        default="en",
        description="User's preferred language"
    )
    query: str
    response: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = None


class FeedbackDB(BaseModel):
    """Feedback model for MongoDB."""
    query_id: str
    session_id: Optional[str] = None
    user_language: str = Field(
        default="en",
        description="User's language preference"
    )
    rating: int
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
