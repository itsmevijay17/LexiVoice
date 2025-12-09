"""
Unified Chat Page - ChatGPT-inspired interface with text and voice.
Fixed UI (no white boxes), Dark Mode bubbles, Legal Sources, Voice Support.
Multilingual support enabled.
"""
import streamlit as st
from streamlit_mic_recorder import mic_recorder
from datetime import datetime
from utils.audio_processor import prepare_audio_for_whisper
from components.language_selector import get_language_name, render_language_selector


def show():
    """Display unified chat interface."""
    
    # ----------- FIXED UI STYLING -----------
    st.markdown("""
    <style>
        /* Hide default Streamlit elements */
        #MainMenu, footer, header {visibility: hidden;}

        /* Page container */
        .block-container {
            padding-top: 0.8rem;
            max-width: 900px;
            margin: auto !important;
        }

        /* Chat message base - Full width bubbles */
        .message {
            padding: 1rem 1.4rem;
            border-radius: 12px;
            margin-bottom: 1.2rem;
            width: 100% !important;          /* force full chat width */
            max-width: 100% !important;       /* prevent shrinking */
            font-size: 0.95rem;
            line-height: 1.5;
        }

        /* ASSISTANT bubble (left, dark) */
        .assistant-message {
            background: #181818 !important;
            margin-right: auto !important;
            color: #E7E7E7 !important;
            border: 1px solid #333;
            width: 100% !important;           /* match text area width */
            max-width: 100% !important;
            border-radius: 16px !important;
        }

        /* USER bubble (right, green) */
        .user-message {
            background: #2E7D32 !important;
            margin-left: auto !important;
            color: #fff !important;
            border: 1px solid #1B5E20;
            width: fit-content !important;      /* let user bubble stay small */
            max-width: 85% !important;          /* wrap if text long */
        }

        /* Remove Streamlit white background layers */
        .stMarkdown, .stMarkdown div, .stChatMessage {
            background: rgba(0,0,0,0) !important;
        }

        /* Expander Style (dark mode) */
        .streamlit-expanderHeader, .streamlit-expanderContent {
            background: #111 !important;
            color: #ddd !important;
        }

        /* Highlighted source box */
        .sources-box {
            background: #1a1a1a !important;
            border-left: 4px solid #4FA3FF;
            color: #ddd !important;
            padding: 0.8rem;
            border-radius: 5px;
            margin-top: 0.4rem;
        }

        /* Audio box styling */
        .audio-response {
            background: #212936 !important;
            padding: 1rem;
            border-radius: 10px;
            margin-top: 0.7rem;
            border: 1px solid #334155;
        }
    </style>
    """, unsafe_allow_html=True)

    # ----------- TOP BAR -----------
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button("⬅️ Back"):
            st.session_state.selected_country = None
            st.rerun()

    with col2:
        flags = {
            'india': '🇮🇳', 'canada': '🇨🇦', 'usa': '🇺🇸', 'uk': '🇬🇧',
            'australia': '🇦🇺', 'japan': '🇯🇵', 'singapore': '🇸🇬', 'uae': '🇦🇪',
            'germany': '🇩🇪', 'france': '🇫🇷', 'spain': '🇪🇸', 'mexico': '🇲🇽',
            'brazil': '🇧🇷', 'newzealand': '🇳🇿', 'hongkong': '🇭🇰', 'thailand': '🇹🇭',
            'malaysia': '🇲🇾', 'southkorea': '🇰🇷', 'indonesia': '🇮🇩'
        }

        country_names = {
            'india': 'India', 'canada': 'Canada', 'usa': 'United States', 'uk': 'United Kingdom',
            'australia': 'Australia', 'japan': 'Japan', 'singapore': 'Singapore', 'uae': 'UAE',
            'germany': 'Germany', 'france': 'France', 'spain': 'Spain', 'mexico': 'Mexico',
            'brazil': 'Brazil', 'newzealand': 'New Zealand', 'hongkong': 'Hong Kong', 'thailand': 'Thailand',
            'malaysia': 'Malaysia', 'southkorea': 'South Korea', 'indonesia': 'Indonesia'
        }

        sel = st.session_state.get('selected_country')
        flag = flags.get(sel, '🌍')
        display_name = country_names.get(sel, sel.upper() if isinstance(sel, str) else 'Global')

        st.markdown(f"""
        <div style="text-align: center; font-size: 1.2rem; font-weight: bold;">
            {flag} {display_name} Legal Assistant
        </div>""", unsafe_allow_html=True)

    with col3:
        if st.button("🚪 Logout"):
            from utils.auth import AuthManager
            AuthManager.logout()
            st.rerun()

    st.markdown("---")

    # ----------- LANGUAGE & COUNTRY INFO -----------
    lang_col1, lang_col2 = st.columns(2)

    with lang_col1:
        st.markdown(f"**🌍 Country:** {st.session_state.selected_country.upper()}")

    with lang_col2:
        # Render language selector component so users can change language
        try:
            selected_code = render_language_selector()
            user_lang = st.session_state.get('user_language', selected_code or 'en')
        except Exception:
            user_lang = st.session_state.get('user_language', 'en')

        lang_name = get_language_name(user_lang)
        st.markdown(f"**🗣️ Language:** {lang_name}")

    # ----------- CHAT HISTORY -----------
    if not st.session_state.chat_history:
        st.markdown(f"""
        <div class="message assistant-message">
            <h3>👋 Hello! I'm your LexiVoice assistant.</h3>
            <p>I provide legal insights for <strong>{st.session_state.selected_country.upper()}</strong>.</p>
            <ul>
                <li>💬 Ask any question</li>
                <li>🎤 Use your voice</li>
                <li>🔊 Receive audio answers</li>
            </ul>
            <p style="font-size: 0.85rem; color: #aaa;">
                Example: "Can I work on a student visa?"
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for entry in st.session_state.chat_history:
            st.markdown(f"""
            <div class="message user-message"><strong>You:</strong><br>{entry['query']}</div>
            """, unsafe_allow_html=True)

            response = entry['response']

            st.markdown(f"""
            <div class="message assistant-message"><strong>LexiVoice:</strong><br>{response.get('answer', '')}</div>
            """, unsafe_allow_html=True)

            with st.expander("🧠 See reasoning"):
                reasoning = response.get('reasoning', 'No reasoning available')
                if '[Voice Query Transcription:' in reasoning:
                    reasoning = reasoning.split('\n\n', 1)[-1]
                st.markdown(reasoning)

            if response.get('sources'):
                with st.expander("📚 View sources"):
                    for i, source in enumerate(response['sources'], 1):
                        st.markdown(f"""
                            <div class="sources-box">
                            <strong>{i}. {source.get('title', 'Unknown')}</strong><br>
                            🔖 Section: {source.get('section', 'N/A')}<br>
                            📌 Relevance: {source.get('relevance_score', 0):.2f}
                            </div>
                        """, unsafe_allow_html=True)

            if response.get('audio_base64'):
                audio_bytes = st.session_state.api_client.decode_audio(response['audio_base64'])
                st.audio(audio_bytes, format="audio/mp3")

            st.markdown("<br>", unsafe_allow_html=True)

    # ----------- INPUT AREA -----------
    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["💬 Type Message", "🎤 Voice Message"])

    # --- TEXT INPUT -----------------
    with tab1:
        col1, col2 = st.columns([5, 1])
        with col1:
            text_query = st.text_input(
                "Ask your question:",
                placeholder="e.g., Can I work on a student visa?",
                label_visibility="collapsed"
            )
        with col2:
            include_audio = st.checkbox("🔊", value=False, help="Get audio answer")

        if st.button("Send", use_container_width=True, type="primary"):
            if text_query:
                with st.spinner("🔍 Processing..."):
                    response = st.session_state.api_client.chat_text(
                        country=st.session_state.selected_country,
                        query=text_query,
                        session_id=st.session_state.user['id'],
                        include_audio=include_audio,
                        user_language=st.session_state.get('user_language', 'en')
                    )
                    if 'error' not in response:
                        st.session_state.chat_history.append({
                            'timestamp': datetime.now(),
                            'query': text_query,
                            'response': response,
                            'type': 'text'
                        })
                        st.rerun()
                    else:
                        st.error(f"Error: {response['error']}")

    # --- VOICE INPUT -----------------
    with tab2:
        st.markdown("🎙️ Click to record your question")
        audio_data = mic_recorder(
            start_prompt="🎤 Start Recording",
            stop_prompt="⏹️ Stop",
            format="wav",
            use_container_width=True
        )

        if audio_data:
            st.success("🎯 Voice recorded!")
            st.audio(audio_data['bytes'], format="audio/wav")

            col1, col2 = st.columns(2)
            with col1:
                include_audio_voice = st.checkbox("🔊 Get audio response", value=True)
            with col2:
                if st.button("🚀 Process Voice", use_container_width=True, type="primary"):
                    with st.spinner("🎤 Transcribing + Analyzing..."):
                        response = st.session_state.api_client.chat_voice(
                            audio_bytes=audio_data['bytes'],
                            country=st.session_state.selected_country,
                            session_id=st.session_state.user['id'],
                            include_audio=include_audio_voice,
                            user_language=st.session_state.get('user_language', 'en')
                        )
                        if 'error' not in response:
                            reasoning = response.get('reasoning', '')
                            transcription = "Unknown"
                            if '[Voice Query Transcription:' in reasoning:
                                transcription = reasoning.split('[Voice Query Transcription:')[1].split("]")[0].strip()

                            st.session_state.chat_history.append({
                                'timestamp': datetime.now(),
                                'query': transcription,
                                'response': response,
                                'type': 'voice'
                            })
                            st.rerun()
                        else:
                            st.error(f"Error: {response['error']}")
