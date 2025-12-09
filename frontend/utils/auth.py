"""
Simple authentication system for LexiVoice.
Stores user data in session state (can be upgraded to database later).
"""
import streamlit as st
import bcrypt
import uuid
from datetime import datetime
from typing import Dict, Optional


# Simple in-memory user store (replace with database in production)
USERS_DB = {}


class AuthManager:
    """Handle user authentication."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def register_user(email: str, password: str, name: str) -> Dict:
        """Register a new user."""
        if email in USERS_DB:
            return {"success": False, "error": "Email already exists"}
        
        user_id = str(uuid.uuid4())
        USERS_DB[email] = {
            'id': user_id,
            'email': email,
            'name': name,
            'password_hash': AuthManager.hash_password(password),
            'created_at': datetime.now().isoformat(),
            'selected_country': None
        }
        
        return {"success": True, "user_id": user_id}
    
    @staticmethod
    def login_user(email: str, password: str) -> Dict:
        """Login user."""
        if email not in USERS_DB:
            return {"success": False, "error": "User not found"}
        
        user = USERS_DB[email]
        if not AuthManager.verify_password(password, user['password_hash']):
            return {"success": False, "error": "Invalid password"}
        
        return {
            "success": True,
            "user": {
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'selected_country': user.get('selected_country')
            }
        }
    
    @staticmethod
    def update_user_country(email: str, country: str):
        """Update user's selected country."""
        if email in USERS_DB:
            USERS_DB[email]['selected_country'] = country
    
    @staticmethod
    def is_authenticated() -> bool:
        """Check if user is authenticated."""
        return 'user' in st.session_state and st.session_state.user is not None
    
    @staticmethod
    def logout():
        """Logout user."""
        st.session_state.user = None
        st.session_state.authenticated = False
        st.session_state.selected_country = None


# Initialize demo users for testing
if not USERS_DB:
    # Create demo user
    AuthManager.register_user(
        email="demo@lexivoice.ai",
        password="demo123",
        name="Demo User"
    )