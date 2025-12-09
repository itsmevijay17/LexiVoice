"""
Language Selector Component - Supports 10+ languages with ISO 639-1 codes.
"""
import streamlit as st


def render_language_selector():
    """
    Display language selector in sidebar/main area.
    
    Returns:
        Selected language code (e.g., 'en', 'hi', 'es')
    """
    
    # Supported languages mapping
    languages = {
        "🇬🇧 English": "en",
        "🇮🇳 हिन्दी (Hindi)": "hi",
        "🇪🇸 Español (Spanish)": "es",
        "🇫🇷 Français (French)": "fr",
        "🇩🇪 Deutsch (German)": "de",
        "🇨🇳 中文 (Chinese - Simplified)": "zh-CN",
        "🇯🇵 日本語 (Japanese)": "ja",
        "🇰🇷 한국어 (Korean)": "ko",
        "🇵🇹 Português (Portuguese)": "pt",
        "🇷🇺 Русский (Russian)": "ru",
        "🇮🇹 Italiano (Italian)": "it",
        "🇳🇱 Nederlands (Dutch)": "nl",
        "🇸🇪 Svenska (Swedish)": "sv",
        "🇵🇱 Polski (Polish)": "pl",
        "🇹🇷 Türkçe (Turkish)": "tr",
    }
    
    # Create language selector
    st.markdown("#### 🗣️ Select Language")
    
    selected_language_display = st.selectbox(
        "Preferred Language",
        options=list(languages.keys()),
        index=0,  # Default to English
        label_visibility="collapsed",
        key="language_selector"
    )
    
    # Get the language code
    selected_language_code = languages[selected_language_display]
    
    # Store in session state
    st.session_state.user_language = selected_language_code
    
    # Display selected language info
    st.caption(f"🎤 Speech & 📝 Responses in {selected_language_display.split()[-1].rstrip(')')}")
    
    return selected_language_code


def get_language_name(language_code: str) -> str:
    """
    Get friendly name for language code.
    
    Args:
        language_code: ISO 639-1 code (e.g., 'en', 'hi')
        
    Returns:
        Friendly language name
    """
    language_names = {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "zh-CN": "Chinese (Simplified)",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "pt": "Portuguese",
        "ru": "Russian",
        "it": "Italian",
        "nl": "Dutch",
        "sv": "Swedish",
        "pl": "Polish",
        "tr": "Turkish",
    }
    return language_names.get(language_code, "Unknown")


def get_supported_languages() -> dict:
    """Get all supported languages."""
    return {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "zh-CN": "Chinese (Simplified)",
        "ja": "Japanese",
        "ko": "Korean",
        "pt": "Portuguese",
        "ru": "Russian",
        "it": "Italian",
        "nl": "Dutch",
        "sv": "Swedish",
        "pl": "Polish",
        "tr": "Turkish",
    }
