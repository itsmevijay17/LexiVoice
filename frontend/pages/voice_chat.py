"""
Voice Chat Page - Speak your questions and hear AI responses.
"""
import streamlit as st
from streamlit_mic_recorder import mic_recorder
from datetime import datetime
import base64


def show():
    """Display voice chat interface."""
    
    st.markdown("### 🎤 Voice Chat")
    st.markdown(f"**Selected Country:** {st.session_state.selected_country.upper()}")
    
    st.info("🎙️ Click the microphone button, speak your question, then click stop. The AI will respond with both text and voice!")
    
    # Audio response toggle (default ON for voice chat)
    include_audio_response = st.checkbox("🔊 Get audio response", value=True)
    
    # Voice recorder
    st.markdown("#### 🎙️ Record Your Question")
    
    audio_data = mic_recorder(
        start_prompt="🎤 Click to start recording",
        stop_prompt="⏹️ Click to stop recording",
        just_once=False,
        use_container_width=True,
        format="wav",
        key="voice_recorder"
    )
    
    # Process recorded audio
    if audio_data:
        st.success("✅ Recording captured!")
        
        # Show recorded audio
        st.markdown("**Your Recording:**")
        st.audio(audio_data['bytes'], format='audio/wav')
        
        # Process button
        if st.button("🚀 Process Voice Query", use_container_width=True):
            with st.spinner("🎤 Transcribing speech... 🤖 Generating answer..."):
                # Call voice API (include user's selected language)
                response = st.session_state.api_client.chat_voice(
                    audio_bytes=audio_data['bytes'],
                    country=st.session_state.selected_country,
                    session_id=st.session_state.session_id,
                    include_audio=include_audio_response,
                    user_language=st.session_state.get('user_language', 'en')
                )
                
                if 'error' in response:
                    st.error(f"❌ Error: {response['error']}")
                else:
                    # Extract transcription from reasoning (we included it there)
                    reasoning = response.get('reasoning', '')
                    if '[Voice Query Transcription:' in reasoning:
                        transcription_part = reasoning.split('[Voice Query Transcription:')[1].split(']')[0]
                        transcription = transcription_part.strip().strip("'\"")
                    else:
                        transcription = "Transcription not available"
                    
                    # Display results
                    st.markdown("---")
                    st.markdown("### 📝 Transcription")
                    st.info(f"**You asked:** {transcription}")
                    
                    st.markdown("### 💬 AI Response")
                    st.success(response.get('answer', 'No answer available'))
                    
                    # Reasoning
                    with st.expander("🧠 See Reasoning"):
                        # Clean reasoning (remove transcription part)
                        clean_reasoning = reasoning.split('\n\n', 1)[-1] if '\n\n' in reasoning else reasoning
                        st.markdown(clean_reasoning)
                    
                    # Sources
                    if response.get('sources'):
                        with st.expander("📚 View Sources"):
                            for i, source in enumerate(response['sources'], 1):
                                st.markdown(f"""
                                **{i}. {source.get('title', 'Unknown')}**
                                - Section: {source.get('section', 'N/A')}
                                - Relevance: {source.get('relevance_score', 0):.2f}
                                """)
                    
                    # Audio response
                    if response.get('audio_base64'):
                        st.markdown("---")
                        st.markdown("### 🔊 Audio Response")
                        st.markdown("**AI speaks:**")
                        
                        audio_bytes = st.session_state.api_client.decode_audio(
                            response['audio_base64']
                        )
                        
                        # Auto-play audio
                        st.audio(audio_bytes, format='audio/mp3', autoplay=True)
                        
                        st.info("🎧 Audio is playing automatically! You can replay it anytime.")
                    
                    # Feedback
                    st.markdown("---")
                    st.markdown("### 📊 Was this helpful?")
                    
                    col1, col2, col3 = st.columns([1, 1, 2])
                    
                    with col1:
                        if st.button("👍 Yes, helpful", use_container_width=True):
                            st.session_state.api_client.submit_feedback(
                                query_id=response.get('query_id'),
                                rating=5,
                                comment="Voice chat - Helpful"
                            )
                            st.success("Thanks for your feedback!")
                    
                    with col2:
                        if st.button("👎 Not helpful", use_container_width=True):
                            st.session_state.api_client.submit_feedback(
                                query_id=response.get('query_id'),
                                rating=2,
                                comment="Voice chat - Not helpful"
                            )
                            st.info("Thanks! We'll improve.")
    
    # Tips
    st.markdown("---")
    st.markdown("### 💡 Tips for Best Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **For clear transcription:**
        - 🎙️ Speak clearly and at normal pace
        - 🔇 Minimize background noise
        - ⏱️ Keep questions under 30 seconds
        - 📝 Be specific in your question
        """)
    
    with col2:
        st.markdown("""
        **Example voice questions:**
        - "Can I work on a student visa?"
        - "What is the minimum wage?"
        - "What are my consumer rights?"
        - "Tell me about work permits"
        """)