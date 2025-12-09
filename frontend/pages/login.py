"""
Login/Landing Page - MongoDB-inspired design with project introduction.
"""
import streamlit as st
from utils.auth import AuthManager


def show():
    """Display login/landing page."""
    
    # Custom CSS for MongoDB-inspired design
    st.markdown("""
    <style>
        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Full-width layout */
        .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
            max-width: 100%;
        }
        
        /* Left panel styling */
        .login-panel {
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a7b 100%);
            padding: 3rem;
            border-radius: 10px;
            color: white;
        }
        
        /* Right panel styling */
        .intro-panel {
            background: linear-gradient(135deg, #0d7377 0%, #14b8a6 100%);
            padding: 3rem;
            border-radius: 10px;
            color: white;
        }
        
        /* Logo styling */
        .logo {
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 1rem;
            text-align: center;
        }
        
        /* Feature box */
        .feature-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            backdrop-filter: blur(10px);
        }
        
        /* Input styling */
        .stTextInput input {
            border-radius: 5px;
            border: 1px solid #ccc;
            padding: 0.5rem;
        }
        
        /* Button styling */
        .stButton>button {
            width: 100%;
            background: #14b8a6;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            padding: 0.75rem;
            border: none;
        }
        
        .stButton>button:hover {
            background: #0d9488;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create two columns
    col1, col2 = st.columns([1, 1], gap="large")
    
    # LEFT PANEL - Login/Signup
    with col1:
        st.markdown('<div class="login-panel">', unsafe_allow_html=True)
        
        # Logo
        st.markdown('<div class="logo">⚖️ LexiVoice</div>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; font-size: 1.2rem; margin-bottom: 2rem;">AI-Powered Legal Assistant</p>', unsafe_allow_html=True)
        
        # Login/Signup tabs
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        # LOGIN TAB
        with tab1:
            st.markdown("### Welcome Back!")
            st.markdown("Log in to access your legal assistant")
            
            with st.form("login_form"):
                email = st.text_input("📧 Email Address", placeholder="your@email.com")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter password")
                
                submit = st.form_submit_button("🚀 Login")
                
                if submit:
                    if email and password:
                        result = AuthManager.login_user(email, password)
                        
                        if result['success']:
                            st.session_state.user = result['user']
                            st.session_state.authenticated = True
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error(f"❌ {result['error']}")
                    else:
                        st.warning("Please enter both email and password")
            
            # Demo credentials
            st.info("""
            **Demo Credentials:**
            - Email: `demo@lexivoice.ai`
            - Password: `demo123`
            """)
        
        # SIGNUP TAB
        with tab2:
            st.markdown("### Create Account")
            st.markdown("Join LexiVoice to get legal answers instantly")
            
            with st.form("signup_form"):
                name = st.text_input("👤 Full Name", placeholder="John Doe")
                email = st.text_input("📧 Email Address", placeholder="your@email.com")
                password = st.text_input("🔒 Password", type="password", placeholder="Create password")
                confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm password")
                
                submit = st.form_submit_button("🎉 Sign Up")
                
                if submit:
                    if name and email and password and confirm_password:
                        if password != confirm_password:
                            st.error("❌ Passwords don't match")
                        elif len(password) < 6:
                            st.error("❌ Password must be at least 6 characters")
                        else:
                            result = AuthManager.register_user(email, password, name)
                            
                            if result['success']:
                                st.success("✅ Account created! Please login.")
                            else:
                                st.error(f"❌ {result['error']}")
                    else:
                        st.warning("Please fill all fields")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # RIGHT PANEL - Project Introduction
    with col2:
        st.markdown('<div class="intro-panel">', unsafe_allow_html=True)
        
        st.markdown("## 🌟 Introducing LexiVoice")
        st.markdown("### Your AI-Powered Multilingual Legal Assistant")
        
        st.markdown("""
        <div class="feature-box">
            <h3>🎯 What is LexiVoice?</h3>
            <p>LexiVoice is an intelligent legal assistant that provides accurate, 
            explainable answers to legal questions across multiple countries. 
            Powered by advanced RAG (Retrieval-Augmented Generation) technology, 
            it combines voice interaction with comprehensive legal knowledge.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-box">
            <h3>✨ Unique Features</h3>
            <ul style="font-size: 1.1rem; line-height: 2rem;">
                <li>🎤 <strong>Voice Interaction</strong> - Speak your questions naturally</li>
                <li>🔊 <strong>Audio Responses</strong> - Hear answers in your language</li>
                <li>🌍 <strong>Multi-Country Support</strong> - India, Canada, USA laws</li>
                <li>📚 <strong>Source Citations</strong> - Transparent, verified answers</li>
                <li>🧠 <strong>Explainable AI</strong> - Understand the reasoning</li>
                <li>⚡ <strong>Fast & Accurate</strong> - RAG-powered responses</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-box">
            <h3>🚀 How It Works</h3>
            <ol style="font-size: 1.1rem; line-height: 2rem;">
                <li>Choose your country (India, Canada, or USA)</li>
                <li>Ask your legal question (text or voice)</li>
                <li>Get instant, accurate answers with sources</li>
                <li>Hear responses in audio format (optional)</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.15); padding: 1.5rem; border-radius: 8px; margin-top: 1rem;">
            <p style="font-size: 0.9rem; margin: 0;">
                <strong>⚠️ Disclaimer:</strong> LexiVoice provides general legal information 
                for educational purposes. It is not a substitute for professional legal advice. 
                Consult a qualified lawyer for specific legal matters.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)