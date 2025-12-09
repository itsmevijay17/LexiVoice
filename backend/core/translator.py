"""
Translation module using googletrans (community package).

This implementation uses `googletrans` (free, unofficial). It includes a
safe fallback so the backend won't crash if `googletrans` is not installed.

If you prefer the paid Google Cloud Translation API, revert to the
`google-cloud-translate` client implementation.
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Try a best-effort top-level import; if it fails, we'll attempt a dynamic import
# inside the handler so we can capture and log detailed exceptions at runtime.
try:
    from googletrans import Translator as GT_Translator, LANGUAGES as GT_LANGUAGES
except Exception as import_exc:
    GT_Translator = None
    GT_LANGUAGES = {}
    logger.debug(f"googletrans top-level import failed: {import_exc}")


class TranslationHandler:
    """Translation handler using googletrans with graceful fallback."""

    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'hi': 'Hindi',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'zh': 'Chinese (Simplified)',
        'ja': 'Japanese',
        'ko': 'Korean',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'it': 'Italian',
        'nl': 'Dutch',
        'sv': 'Swedish',
        'pl': 'Polish',
        'tr': 'Turkish',
        'ar': 'Arabic',
        'te': 'Telugu',
        'ta': 'Tamil',
        'bn': 'Bengali',
    }

    def __init__(self):
        # If the top-level import failed earlier, try importing dynamically now
        if GT_Translator is None:
            try:
                from googletrans import Translator as GT_Translator_local, LANGUAGES as GT_LANGUAGES_local
                try:
                    self.translator = GT_Translator_local()
                    # update module-level references for any future handlers
                    globals()['GT_Translator'] = GT_Translator_local
                    globals()['GT_LANGUAGES'] = GT_LANGUAGES_local
                    logger.info("🌍 googletrans Translator dynamically initialized")
                except Exception as e:
                    logger.error(f"❌ Failed to instantiate googletrans Translator after dynamic import: {e}")
                    self.translator = None
            except Exception as dyn_exc:
                # googletrans import failed; try a lightweight fallback (deep_translator)
                logger.debug(f"googletrans dynamic import failed: {dyn_exc}")
                try:
                    from deep_translator import GoogleTranslator as DeepGoogleTranslator
                    try:
                        # We'll use deep-translator for translations (no httpx/httpcore dependency)
                        self.translator = DeepGoogleTranslator(source='auto', target='en')
                        globals()['GT_Translator'] = None
                        globals()['GT_LANGUAGES'] = {}
                        # mark that we are using deep-translator (handle in translate_text)
                        self._use_deep_translator = True
                        logger.info("🌍 deep-translator GoogleTranslator initialized as fallback")
                    except Exception as e2:
                        logger.error(f"❌ Failed to initialize deep_translator: {e2}")
                        self.translator = None
                        self._use_deep_translator = False
                except Exception as e3:
                    logger.warning(f"⚠️ Translator imports failed at runtime: {dyn_exc}; {e3}. Translator disabled. Install `googletrans==4.0.0-rc1` or `deep-translator` in the backend venv to enable.")
                    self.translator = None
                    self._use_deep_translator = False
        else:
            try:
                self.translator = GT_Translator()
                logger.info("🌍 googletrans Translator initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize googletrans translator: {e}")
                self.translator = None
        # Ensure flag exists
        if not hasattr(self, '_use_deep_translator'):
            self._use_deep_translator = False

    def detect_language(self, text: str) -> Dict:
        if not text:
            return {'language': 'en', 'confidence': 0.0, 'language_name': 'English', 'success': False, 'error': 'No text provided'}

        if not self.translator:
            return {'language': 'en', 'confidence': 0.0, 'language_name': 'English', 'success': False, 'error': 'Translator not available'}

        try:
            detection = self.translator.detect(text)
            lang = getattr(detection, 'lang', None) or (detection[0].lang if isinstance(detection, (list, tuple)) else None)
            conf = getattr(detection, 'confidence', None) or (detection[0].confidence if isinstance(detection, (list, tuple)) else 0.0)
            language_name = self.SUPPORTED_LANGUAGES.get(lang, GT_LANGUAGES.get(lang, lang))

            return {'language': lang, 'confidence': conf, 'language_name': language_name, 'success': True}
        except Exception as e:
            logger.error(f"❌ googletrans detect failed: {e}")
            return {'language': 'en', 'confidence': 0.0, 'language_name': 'English', 'success': False, 'error': str(e)}

    def translate_text(self, text: str, target_lang: str = 'en', source_lang: Optional[str] = None) -> Dict:
        if not text:
            return {'text': '', 'source_lang': 'unknown', 'target_lang': target_lang, 'translated': False, 'original_text': '', 'error': 'Empty text provided', 'success': False}

        if not self.translator:
            logger.warning("⚠️ Translator not available; returning original text")
            return {'text': text, 'source_lang': source_lang or 'unknown', 'target_lang': target_lang, 'translated': False, 'original_text': text, 'error': 'Translator not available', 'success': False}

        try:
            # Auto-detect if needed
            if source_lang is None or source_lang == 'auto':
                det = self.detect_language(text)
                source_lang = det.get('language', 'auto')
                confidence = det.get('confidence', 0.0)
            else:
                confidence = 1.0

            if source_lang == target_lang:
                return {'text': text, 'source_lang': source_lang, 'target_lang': target_lang, 'translated': False, 'original_text': text, 'confidence': confidence, 'note': 'Source and target languages match', 'success': True}

            # If we're using googletrans (GT_Translator) -> use its API
            if not self._use_deep_translator and getattr(self, 'translator', None) is not None:
                # googletrans.translate(text, dest='en', src='auto')
                trans = self.translator.translate(text, dest=target_lang, src=source_lang if source_lang and source_lang != 'auto' else 'auto')
                translated_text = getattr(trans, 'text', None) or (trans[0].text if isinstance(trans, (list, tuple)) else str(trans))
            else:
                # Fallback: use deep-translator (requests-based) which doesn't provide detection
                try:
                    # If source_lang is not provided, attempt language detection via langdetect
                    if source_lang is None or source_lang == 'auto':
                        try:
                            from langdetect import detect
                            detected = detect(text)
                            source_lang = detected
                        except Exception:
                            source_lang = 'auto'

                    # deep_translator's GoogleTranslator supports init with source & target
                    from deep_translator import GoogleTranslator as DeepGoogleTranslator
                    dt = DeepGoogleTranslator(source=source_lang if source_lang and source_lang != 'auto' else 'auto', target=target_lang)
                    translated_text = dt.translate(text)
                except Exception as e:
                    logger.error(f"❌ deep-translator translate failed: {e}")
                    return {'text': text, 'source_lang': source_lang or 'unknown', 'target_lang': target_lang, 'translated': False, 'original_text': text, 'error': str(e), 'success': False}

            return {'text': translated_text, 'source_lang': source_lang, 'target_lang': target_lang, 'translated': True, 'original_text': text, 'confidence': confidence, 'success': True}

        except Exception as e:
            logger.error(f"❌ googletrans translate failed: {e}")
            return {'text': text, 'source_lang': source_lang or 'unknown', 'target_lang': target_lang, 'translated': False, 'original_text': text, 'error': str(e), 'success': False}

    def translate_query_to_english(self, query: str, user_language: str = 'en') -> Dict:
        logger.info(f"📝 Translating query to English (from {user_language})")
        return self.translate_text(text=query, target_lang='en', source_lang=user_language)

    def translate_answer_to_user_language(self, answer: str, user_language: str = 'en') -> Dict:
        logger.info(f"📝 Translating answer from English to {user_language}")
        return self.translate_text(text=answer, target_lang=user_language, source_lang='en')

    def get_supported_languages(self) -> Dict[str, str]:
        return self.SUPPORTED_LANGUAGES.copy()

    def is_language_supported(self, language_code: str) -> bool:
        return language_code in self.SUPPORTED_LANGUAGES

    def get_language_name(self, language_code: str) -> str:
        return self.SUPPORTED_LANGUAGES.get(language_code, GT_LANGUAGES.get(language_code, 'Unknown'))


# Global translator instance
_translator_instance = None


def get_translator() -> TranslationHandler:
    global _translator_instance
    if _translator_instance is None:
        logger.info("🔄 Initializing global translator instance (googletrans)...")
        _translator_instance = TranslationHandler()
    return _translator_instance
