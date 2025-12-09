"""
Chat router - Main RAG endpoint with optional TTS & voice support.
"""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from typing import Optional
from pymongo.database import Database
from datetime import datetime
from typing import Dict, Any
import time
import logging

from backend.core.schemas import ChatRequest, ChatResponse, SourceDocument
from backend.core.database import get_database
from backend.core.retriever import get_retriever
from backend.core.llm_handler import get_llm_handler
from backend.core.text_to_speech import get_tts_handler   # ← TTS handler used by text endpoint
from backend.core.translator import get_translator   # ← Translation handler for multilingual support
from backend.core.crud import QueryLogCRUD

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest,
    db: Database = Depends(get_database)
) -> ChatResponse:
    """
    Main chat endpoint - Complete RAG pipeline with optional TTS.

    Flow:
    1. Retrieve documents (FAISS)
    2. Generate answer (Groq)
    3. Convert to TTS (optional)
    4. Save to DB
    5. Return structured response
    """
    start_time = time.time()

    logger.info("📝 New chat request:")
    logger.info(f"   Country: {request.country}")
    logger.info(f"   Language: {request.user_language}")
    logger.info(f"   Query: {request.query}")
    logger.info(f"   Include audio: {getattr(request, 'include_audio', False)}")
    logger.info(f"   Session: {request.session_id}")

    try:
        # ------------------------------------------------------------
        # STEP 0 — TRANSLATE QUERY TO ENGLISH (if needed)
        # ------------------------------------------------------------
        query_for_rag = request.query
        original_query = request.query
        
        if request.user_language != 'en':
            logger.info(f"🌍 Step 0: Translating query to English ({request.user_language} → en)...")
            try:
                translator = get_translator()
                translation_result = translator.translate_query_to_english(
                    query=request.query,
                    user_language=request.user_language
                )
                
                if translation_result.get('success'):
                    query_for_rag = translation_result['text']
                    logger.info(f"✅ Query translated: '{query_for_rag}'")
                else:
                    logger.warning(f"⚠️ Translation failed, using original query: {translation_result.get('error')}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Translation service error (non-critical): {e}")
                query_for_rag = request.query
        else:
            logger.info("ℹ️ Query already in English, skipping translation")
        
        # ------------------------------------------------------------
        # STEP 1 — DOCUMENT RETRIEVAL
        # ------------------------------------------------------------
        logger.info("📚 Step 1: Retrieving documents...")

        try:
            retriever = get_retriever(request.country.value)
            retrieved_chunks = retriever.search(query_for_rag, top_k=3)

            if not retrieved_chunks:
                logger.warning("⚠️ No relevant documents found")
                return _create_no_results_response(request, db, start_time)

            logger.info(f"✅ Retrieved {len(retrieved_chunks)} documents")

        except Exception as e:
            logger.error(f"❌ Retrieval failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Document retrieval failed: {str(e)}"
            )

        # ------------------------------------------------------------
        # STEP 2 — LLM ANSWER GENERATION
        # ------------------------------------------------------------
        logger.info("🤖 Step 2: Generating answer...")

        try:
            llm = get_llm_handler()
            answer_dict = llm.generate_answer(
                query=query_for_rag,
                retrieved_chunks=retrieved_chunks,
                country=request.country.value
            )

            if "error" in answer_dict:
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM Error: {answer_dict['error']}"
                )

            logger.info("✅ Answer generated successfully")

        except Exception as e:
            logger.error(f"❌ LLM generation failed: {e}")
            raise HTTPException(500, f"Answer generation failed: {str(e)}")

        # ------------------------------------------------------------
        # STEP 3.5 — TRANSLATE ANSWER TO USER LANGUAGE (if needed)
        # ------------------------------------------------------------
        answer_text = answer_dict.get("answer", "No answer generated")
        reasoning_text = answer_dict.get("reasoning", "No reasoning provided")
        
        if request.user_language != 'en':
            logger.info(f"🌍 Step 3.5: Translating answer to user language (en → {request.user_language})...")
            try:
                translator = get_translator()
                
                # Translate answer
                answer_translation = translator.translate_answer_to_user_language(
                    answer=answer_text,
                    user_language=request.user_language
                )
                
                if answer_translation.get('success'):
                    answer_text = answer_translation['text']
                    logger.info(f"✅ Answer translated")
                else:
                    logger.warning(f"⚠️ Answer translation failed: {answer_translation.get('error')}")
                
                # Translate reasoning
                reasoning_translation = translator.translate_answer_to_user_language(
                    answer=reasoning_text,
                    user_language=request.user_language
                )
                
                if reasoning_translation.get('success'):
                    reasoning_text = reasoning_translation['text']
                    logger.info(f"✅ Reasoning translated")
                else:
                    logger.warning(f"⚠️ Reasoning translation failed: {reasoning_translation.get('error')}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Translation service error (non-critical): {e}")
        else:
            logger.info("ℹ️ Answer already in English, skipping translation")
        
        # ------------------------------------------------------------
        # STEP 4 — OPTIONAL TEXT-TO-SPEECH (TTS)
        # ------------------------------------------------------------
        audio_base64 = None
        audio_format = None

        if getattr(request, "include_audio", False):
            logger.info("🔊 Step 4: Converting answer to audio...")
            try:
                tts = get_tts_handler()
                tts_result = tts.convert_answer_to_audio(
                    answer_text=answer_text,
                    country=request.country.value,
                    include_reasoning=False,
                    language=request.user_language
                )

                if "audio_base64" in tts_result:
                    audio_base64 = tts_result["audio_base64"]
                    audio_format = tts_result.get("format", "mp3")
                    logger.info("✅ Audio generated successfully")
                else:
                    logger.warning(f"⚠️ Audio generation returned no audio: {tts_result}")

            except Exception as e:
                logger.error(f"⚠️ TTS failed (non-critical): {e}")

        # ------------------------------------------------------------
        # STEP 5 — FORMAT SOURCES
        # ------------------------------------------------------------
        logger.info("📋 Step 5: Formatting sources...")
        sources = _format_sources(retrieved_chunks, answer_dict.get("sources", []))

        # ------------------------------------------------------------
        # STEP 6 — BUILD RESPONSE
        # ------------------------------------------------------------
        processing_time = (time.time() - start_time) * 1000

        response_data = {
            "answer": answer_text,
            "reasoning": reasoning_text,
            "sources": sources,
            "country": request.country.value,
            "user_language": request.user_language,
            "timestamp": datetime.utcnow(),
            "confidence_score": _map_confidence_to_score(answer_dict.get("confidence", "medium")),
            "audio_base64": audio_base64,
            "audio_format": audio_format
        }

        # ------------------------------------------------------------
        # STEP 7 — SAVE TO DATABASE
        # ------------------------------------------------------------
        logger.info("💾 Step 6: Saving to database...")

        # convert Pydantic objects to dicts for storage if necessary
        response_data["sources"] = [
            s.model_dump() if hasattr(s, "model_dump") else s
            for s in response_data["sources"]
        ]

        try:
            query_id = QueryLogCRUD.create_query_log(
                db=db,
                session_id=request.session_id,
                country=request.country.value,
                user_language=request.user_language,
                query=original_query,
                response=response_data,
                processing_time_ms=processing_time
            )
            response_data["query_id"] = query_id
            logger.info(f"✅ Saved to database with ID: {query_id}")

        except Exception as e:
            logger.error(f"⚠️ DB save failed: {e}")
            response_data["query_id"] = "unsaved"

        # ------------------------------------------------------------
        # STEP 8 — RETURN RESPONSE
        # ------------------------------------------------------------
        logger.info(f"✅ Request completed in {processing_time:.0f}ms")
        return ChatResponse(**response_data)

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(500, f"Unexpected error: {str(e)}")


# ------------------------------------------------------------------
# Voice endpoint (new) - inserted before the health endpoint (Option C)
# ------------------------------------------------------------------
@router.post("/voice", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_voice(
    audio_file: UploadFile = File(..., description="Audio file (mp3, wav, m4a, webm, etc.)"),
    country: str = Form(..., description="Country code (india/canada/usa)"),
    user_language: str = Form("en", description="User's preferred language (ISO 639-1 code)"),
    session_id: Optional[str] = Form(None, description="Session ID for tracking"),
    include_audio: bool = Form(False, description="Include TTS audio in response"),
    db: Database = Depends(get_database)
) -> ChatResponse:
    """
    Voice chat endpoint - Accept audio input, return text/audio response.

    Complete voice-to-voice flow:
    1. Receive audio file (voice query)
    2. Transcribe to text (Whisper STT)
    3. Process through RAG pipeline
    4. Optionally convert answer to audio (TTS)
    5. Return response with transcription

    Args:
        audio_file: Audio file upload
        country: Country for legal context
        session_id: Optional session ID
        include_audio: Whether to include audio response
        db: Database instance

    Returns:
        ChatResponse with transcription and answer
    """
    from backend.core.speech_to_text import get_stt_handler

    start_time = time.time()

    logger.info(f"🎤 New voice chat request:")
    logger.info(f"   File: {audio_file.filename}")
    logger.info(f"   Country: {country}")
    logger.info(f"   Language: {user_language}")
    logger.info(f"   Include audio response: {include_audio}")

    try:
        # Step 1: Transcribe audio to text
        logger.info("🎤 Step 1: Transcribing audio (Whisper STT)...")

        try:
            stt_handler = get_stt_handler()

            # Transcribe with user language hint (if provided), falling back to country hints
            transcription_result = stt_handler.transcribe_with_fallback(
                audio_file,
                country=country,
                user_language=user_language
            )

            if not transcription_result['success']:
                stt_error = transcription_result.get('error', 'Unknown error')
                logger.error(f"❌ Transcription failed: {stt_error}")
                # Helpful error message for users when STT returned short/punctuation-only text
                user_message = stt_error
                if transcription_result.get('text'):
                    txt = transcription_result.get('text').strip()
                    if len(txt) < 5:
                        user_message = (
                            "Transcription too short or not meaningful. "
                            "Please speak clearly for a few seconds or try selecting the correct language before recording."
                        )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Audio transcription failed: {user_message}"
                )

            query_text = transcription_result['text']

            logger.info(f"✅ Transcription successful")
            logger.info(f"   Transcribed text: {query_text}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ STT processing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Speech-to-text conversion failed: {str(e)}"
            )

        # Step 2: If necessary, detect language of the transcription and translate to English for RAG
        try:
            translator = get_translator()
            detection = translator.detect_language(query_text)
            detected_lang = detection.get('language', 'en')
            logger.info(f"🎤 Detected transcription language: {detected_lang} (confidence: {detection.get('confidence')})")
        except Exception as e:
            logger.warning(f"⚠️ Language detection failed: {e}")
            detected_lang = 'en'

        # If transcription language is not English, translate the query to English for retrieval
        query_for_rag = query_text
        if detected_lang and detected_lang != 'en':
            logger.info(f"🌍 Translating transcribed query to English for retrieval ({detected_lang} → en)...")
            try:
                trans_to_en = translator.translate_query_to_english(query=query_text, user_language=detected_lang)
                if trans_to_en.get('success'):
                    query_for_rag = trans_to_en['text']
                    logger.info(f"✅ Translated transcribed query for RAG: '{query_for_rag}'")
                else:
                    logger.warning(f"⚠️ Translation failed, using original transcription: {trans_to_en.get('error')}")
            except Exception as e:
                logger.warning(f"⚠️ Translation error when translating transcription: {e}")

        # Step 3: Create ChatRequest from transcribed text
        try:
            from backend.core.schemas import CountryEnum

            chat_request = ChatRequest(
                country=CountryEnum(country),
                query=query_text,
                user_language=user_language,
                session_id=session_id,
                include_audio=include_audio
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid country code: {country}"
            )

        # Step 3-7: Process through normal RAG pipeline
        # (Reuse the logic from the text chat endpoint)

        logger.info("📚 Step 2: Retrieving documents...")

        # Ensure query_for_rag is set. Prefer the detected-language translation if available.
        if not query_for_rag:
            query_for_rag = chat_request.query

        # If we don't already have a translation and the user's preferred language isn't English,
        # translate the original chat request query to English (fallback path)
        if (query_for_rag == chat_request.query) and (user_language != 'en'):
            logger.info(f"🌍 Translating query to English ({user_language} → en)...")
            try:
                translator = get_translator()
                translation_result = translator.translate_query_to_english(
                    query=chat_request.query,
                    user_language=user_language
                )
                if translation_result.get('success'):
                    query_for_rag = translation_result['text']
                    logger.info(f"✅ Query translated: '{query_for_rag}'")
                else:
                    logger.warning(f"⚠️ Translation failed: {translation_result.get('error')}")
            except Exception as e:
                logger.warning(f"⚠️ Translation error: {e}")

        try:
            retriever = get_retriever(chat_request.country.value)
            retrieved_chunks = retriever.search(query_for_rag, top_k=3)

            if not retrieved_chunks:
                logger.warning("⚠️ No relevant documents found")
                response = _create_no_results_response(chat_request, db, start_time)
                # Add transcription info
                # Prepend voice transcription to reasoning then return
                response.reasoning = f"[Voice Query: '{query_text}'] " + response.reasoning
                return response

            logger.info(f"✅ Retrieved {len(retrieved_chunks)} documents")

        except Exception as e:
            logger.error(f"❌ Retrieval failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document retrieval failed: {str(e)}"
            )

        logger.info("🤖 Step 3: Generating answer...")

        try:
            llm_handler = get_llm_handler()
            answer_dict = llm_handler.generate_answer(
                query=query_for_rag,
                retrieved_chunks=retrieved_chunks,
                country=chat_request.country.value
            )

            if 'error' in answer_dict:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Answer generation failed: {answer_dict['error']}"
                )

            logger.info("✅ Answer generated successfully")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ LLM generation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Answer generation failed: {str(e)}"
            )

        # Step 4: Convert to audio if requested
        audio_base64 = None
        audio_format = None
        
        # Translate answer to user language if needed
        answer_text = answer_dict.get('answer', 'No answer generated')
        reasoning_text = answer_dict.get('reasoning', 'No reasoning provided')
        
        if user_language != 'en':
            logger.info(f"🌍 Translating answer to user language (en → {user_language})...")
            try:
                translator = get_translator()
                
                answer_translation = translator.translate_answer_to_user_language(
                    answer=answer_text,
                    user_language=user_language
                )
                if answer_translation.get('success'):
                    answer_text = answer_translation['text']
                    logger.info(f"✅ Answer translated")
                else:
                    logger.warning(f"⚠️ Answer translation failed: {answer_translation.get('error')}")
                
                reasoning_translation = translator.translate_answer_to_user_language(
                    answer=reasoning_text,
                    user_language=user_language
                )
                if reasoning_translation.get('success'):
                    reasoning_text = reasoning_translation['text']
                    logger.info(f"✅ Reasoning translated")
                else:
                    logger.warning(f"⚠️ Reasoning translation failed")
            except Exception as e:
                logger.warning(f"⚠️ Translation error: {e}")

        if include_audio:
            logger.info("🔊 Step 5: Converting answer to audio (TTS)...")

            try:
                from backend.core.text_to_speech import get_tts_handler

                tts_handler = get_tts_handler()
                audio_result = tts_handler.convert_answer_to_audio(
                    answer_text=answer_text,
                    country=chat_request.country.value,
                    include_reasoning=False,
                    language=user_language
                )

                if 'audio_base64' in audio_result:
                    audio_base64 = audio_result['audio_base64']
                    audio_format = audio_result.get('format', 'mp3')
                    logger.info(f"✅ Audio generated")

            except Exception as e:
                logger.error(f"⚠️ TTS failed (non-critical): {e}")

        # Step 5: Format response
        sources = _format_sources(retrieved_chunks, answer_dict.get('sources', []))
        processing_time = (time.time() - start_time) * 1000

        response_data = {
            'answer': answer_text,
            'reasoning': f"[Voice Query Transcription: '{query_text}']\n\n" + reasoning_text,
            'sources': sources,
            'country': chat_request.country.value,
            'user_language': user_language,
            'timestamp': datetime.utcnow(),
            'confidence_score': _map_confidence_to_score(answer_dict.get('confidence', 'medium')),
            'audio_base64': audio_base64,
            'audio_format': audio_format
        }

        # Step 6: Save to database
        logger.info("💾 Step 6: Saving to database...")

        # convert Pydantic objects to dicts for storage if necessary
        response_data["sources"] = [
            s.model_dump() if hasattr(s, "model_dump") else s
            for s in response_data["sources"]
        ]

        try:
            query_id = QueryLogCRUD.create_query_log(
                db=db,
                session_id=session_id,
                country=chat_request.country.value,
                user_language=user_language,
                query=query_text,  # Save transcribed text
                response=response_data,
                processing_time_ms=processing_time
            )

            response_data['query_id'] = query_id
            logger.info(f"✅ Saved to database with ID: {query_id}")

        except Exception as e:
            logger.error(f"⚠️ Database save failed: {e}")
            response_data['query_id'] = "unsaved"

        logger.info(f"✅ Voice request completed in {processing_time:.0f}ms")
        logger.info(f"   Transcribed: '{query_text}'")
        logger.info(f"   Audio response: {'Yes' if audio_base64 else 'No'}")

        return ChatResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in voice chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# ------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------
def _format_sources(retrieved_chunks: list, llm_sources: list) -> list:
    """Convert FAISS chunks → SourceDocument list."""
    sources, seen = [], set()

    for chunk in retrieved_chunks[:3]:
        title = chunk.get("title", "Unknown")
        if title not in seen:
            sources.append(
                SourceDocument(
                    title=title,
                    section=chunk.get("section"),
                    url=chunk.get("source_url"),
                    relevance_score=chunk.get("similarity_score")
                )
            )
            seen.add(title)

    return sources


def _map_confidence_to_score(confidence: str) -> float:
    mapping = {"high": 0.9, "medium": 0.7, "low": 0.5}
    return mapping.get(confidence.lower(), 0.7)


def _create_no_results_response(request: ChatRequest, db: Database, start: float) -> ChatResponse:
    """Handle case where FAISS returns no documents."""
    processing_time = (time.time() - start) * 1000

    response = {
        "answer": f"No legal documents matched your question: '{request.query}'.",
        "reasoning": "Try rephrasing your query or ask a different topic.",
        "sources": [],
        "country": request.country.value,
        "user_language": request.user_language,
        "timestamp": datetime.utcnow(),
        "confidence_score": 0.0,
        "audio_base64": None,
        "audio_format": None
    }

    try:
        response["query_id"] = QueryLogCRUD.create_query_log(
            db=db,
            session_id=request.session_id,
            country=request.country.value,
            user_language=request.user_language,
            query=request.query,
            response=response,
            processing_time_ms=processing_time
        )
    except Exception:
        response["query_id"] = "unsaved"

    return ChatResponse(**response)


@router.get("/health")
async def health_check():
    return {
        "service": "chat",
        "status": "healthy",
        "components": {
            "retriever": "ready",
            "llm": "ready",
            "tts": "ready",   # ← NEW
            "database": "ready"
        }
    }
