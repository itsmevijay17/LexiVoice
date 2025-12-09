"""
Text Chat Page - Type your legal questions and get answers.
"""
import streamlit as st
import base64
from datetime import datetime


def show():
    """Display text chat interface."""
    
    st.markdown("### 💬 Ask Your Legal Question")
    st.markdown(f"**Selected Country:** {st.session_state.selected_country.upper()}")
    
    # Audio response toggle
    include_audio = st.checkbox("🔊 Include audio response", value=False)
    
    # Chat input
    query = st.text_input(
        "Your question:",
        placeholder="e.g., Can I work on a student visa?",
        key="text_query_input"
    )
    
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        ask_button = st.button("🚀 Ask", use_container_width=True)
    
    with col2:
        clear_button = st.button("🗑️ Clear History", use_container_width=True)
    
    if clear_button:
        st.session_state.chat_history = []
        st.rerun()
    
    # Process query
    if ask_button and query:
        with st.spinner("🔍 Searching legal documents and generating answer..."):
            # Call API
            response = st.session_state.api_client.chat_text(
                country=st.session_state.selected_country,
                query=query,
                session_id=st.session_state.session_id,
                include_audio=include_audio
            )
            
            if 'error' in response:
                st.error(f"❌ Error: {response['error']}")
            else:
                # Add to chat history
                chat_entry = {
                    'timestamp': datetime.now(),
                    'query': query,
                    'response': response,
                    'type': 'text'
                }
                st.session_state.chat_history.append(chat_entry)
                st.rerun()
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("---")
        st.markdown("### 💬 Conversation History")
        
        for idx, entry in enumerate(reversed(st.session_state.chat_history)):
            with st.container():
                # User query
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>You:</strong> {entry['query']}
                </div>
                """, unsafe_allow_html=True)
                
                # Bot response
                response = entry['response']
                
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>LexiVoice:</strong><br>
                    {response.get('answer', 'No answer available')}
                </div>
                """, unsafe_allow_html=True)
                
                # Reasoning
                with st.expander("🧠 See Reasoning"):
                    st.markdown(response.get('reasoning', 'No reasoning provided'))
                
                # Sources
                if response.get('sources'):
                    with st.expander("📚 View Sources"):
                        for i, source in enumerate(response['sources'], 1):
                            st.markdown(f"""
                            **{i}. {source.get('title', 'Unknown')}**
                            - Section: {source.get('section', 'N/A')}
                            - Relevance: {source.get('relevance_score', 0):.2f}
                            """)
                            if source.get('url'):
                                st.markdown(f"[View Document]({source['url']})")
                
                # Audio response
                if response.get('audio_base64'):
                    st.markdown("🔊 **Audio Response:**")
                    audio_bytes = st.session_state.api_client.decode_audio(
                        response['audio_base64']
                    )
                    st.audio(audio_bytes, format='audio/mp3')
                
                # Feedback
                feedback_col1, feedback_col2, feedback_col3 = st.columns([2, 2, 3])
                
                with feedback_col1:
                    if st.button("👍 Helpful", key=f"thumbs_up_{idx}"):
                        st.session_state.api_client.submit_feedback(
                            query_id=response.get('query_id'),
                            rating=5,
                            comment="Helpful"
                        )
                        st.success("Thanks for your feedback!")
                
                with feedback_col2:
                    if st.button("👎 Not Helpful", key=f"thumbs_down_{idx}"):
                        st.session_state.api_client.submit_feedback(
                            query_id=response.get('query_id'),
                            rating=2,
                            comment="Not helpful"
                        )
                        st.info("Thanks! We'll improve.")
                
                st.markdown("---")
    else:
        st.info("💡 Start by asking a legal question above!")
        
        # Example questions
        st.markdown("### 📝 Example Questions:")
        examples = {
            'india': [
                "What is the minimum wage in India?",
                "Can I work on a student visa in India?",
                "What are my consumer rights for defective products?"
            ],
            'canada': [
                "How many hours can international students work?",
                "What is the federal minimum wage in Canada?",
                "What is the duration of a post-graduation work permit?"
            ],
            'usa': [
                "Can F1 students work off-campus?",
                "What are H1B visa requirements?",
                "What is the federal minimum wage in the USA?"
            ]
        }
        
        for example in examples.get(st.session_state.selected_country, []):
            if st.button(f"💡 {example}", key=f"example_{example}"):
                st.session_state.text_query_input = example
                st.rerun()