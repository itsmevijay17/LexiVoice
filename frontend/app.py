"""
LexiVoice - AI-Powered Multilingual Legal Assistant
Main Streamlit Application (Updated Navigation UI)
"""

import streamlit as st
import sys
import os
import uuid

# Add frontend utilities path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.api_client import LexiVoiceAPI
from utils.auth import AuthManager

# Disable Streamlit default multipage navigation - More aggressive
st.markdown("""
    <style>
    /* Hide sidebar navigation completely */
    section[data-testid="stSidebarNav"] {display: none !important;}
    
    /* Hide all navigation links */
    nav[aria-label="Page navigation"] {display: none !important;}
    
    /* Hide page selection dropdown */
    [data-testid="stPageContainer"] {display: block !important;}
    [data-testid="stSidebarNav"] li {display: none !important;}
    </style>
""", unsafe_allow_html=True)


# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(
    page_title="LexiVoice - Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# -----------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------
if "api_client" not in st.session_state:
    st.session_state.api_client = LexiVoiceAPI()

if "auth_manager" not in st.session_state:
    st.session_state.auth_manager = AuthManager()

if "user" not in st.session_state:
    st.session_state.user = None

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "selected_country" not in st.session_state:
    st.session_state.selected_country = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "current_page" not in st.session_state:
    st.session_state.current_page = "login"

if "user_language" not in st.session_state:
    st.session_state.user_language = "en"


# -----------------------------------------------------
# PAGE ROUTING LOGIC (AUTH → COUNTRY → MAIN UI)
# -----------------------------------------------------
if not st.session_state.authenticated:
    import pages.login as login
    login.show()
    st.stop()

elif st.session_state.selected_country is None:
    import pages.country_selection as country_selection
    country_selection.show()
    st.stop()


# -----------------------------------------------------
# RESTORE SIDEBAR AFTER LOGIN + COUNTRY
# -----------------------------------------------------
st.set_page_config(
    page_title="LexiVoice - Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# Sidebar is hidden - only chat interface shown


# -----------------------------------------------------
# MAIN HEADER
# -----------------------------------------------------
st.markdown('<div style="font-size:2.5rem;font-weight:700;text-align:center;">⚖️ LexiVoice</div>', unsafe_allow_html=True)
st.markdown('<div style="font-size:1.2rem;color:#7a7a7a;text-align:center;margin-bottom:1.8rem;">AI-Powered Multilingual Legal Assistant</div>', unsafe_allow_html=True)


# -----------------------------------------------------
# ALWAYS ROUTE TO MAIN CHAT PAGE (APP ONLY)
# -----------------------------------------------------
import pages.unified_chat as unified_chat
unified_chat.show()
