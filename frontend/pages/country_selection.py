"""
Country Selection Page - Professional grid-based country selector with 20 countries.
Clickable cards without separate select buttons.
"""
import streamlit as st
from utils.auth import AuthManager


def show():
    """Display country selection page."""
    
    # Custom CSS for professional design
    st.markdown("""
    <style>
        /* Hide default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        .country-page {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        /* Header */
        .page-header {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        .page-header h1 {
            font-size: 3rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
            font-weight: 800;
            letter-spacing: -0.5px;
        }
        
        .page-header p {
            font-size: 1.1rem;
            color: #a0aec0;
            margin: 0.5rem 0;
        }
        
        .page-subtitle {
            font-size: 0.95rem;
            color: #718096;
            margin-top: 0.5rem;
        }
        
        /* Grid container - 4 columns */
        .country-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 2rem;
            margin-bottom: 2rem;
            margin-top: 2rem;
        }
        
        @media (max-width: 1200px) {
            .country-grid { grid-template-columns: repeat(3, 1fr); }
        }
        
        @media (max-width: 768px) {
            .country-grid { grid-template-columns: repeat(2, 1fr); }
        }
        
        /* Country card */
        .country-card-wrapper {
            cursor: pointer;
        }
        
        .country-card {
            position: relative;
            border-radius: 16px;
            padding: 1.8rem;
            color: white;
            cursor: pointer;
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            border: 0px solid transparent;
            overflow: hidden;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin-top: 12px;
        }
        
        .country-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0) 100%);
            pointer-events: none;
        }
        
        .country-card:hover {
            transform: translateY(-12px) scale(1.02);
            box-shadow: 0 25px 60px rgba(0,0,0,0.6);
            border: 1px solid rgba(255,255,255,0.25);
        }
        
        .country-card-content {
            position: relative;
            z-index: 1;
        }
        
        .country-flag {
            font-size: 4rem;
            margin-bottom: 0.8rem;
            display: block;
            text-align: center;
        }
        
        .country-name {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            text-align: center;
        }
        
        .country-description {
            font-size: 0.85rem;
            opacity: 0.9;
            margin-bottom: 1rem;
            line-height: 1.5;
            text-align: center;
        }
        
        .country-features {
            font-size: 0.75rem;
            opacity: 0.8;
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            justify-content: center;
        }
        
        .feature-badge {
            background: rgba(255,255,255,0.2);
            padding: 0.35rem 0.75rem;
            border-radius: 20px;
            white-space: nowrap;
            font-weight: 500;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        /* Country specific gradients */
        .india-card { background: linear-gradient(135deg, #FF9933 0%, #138808 100%); }
        .canada-card { background: linear-gradient(135deg, #FF0000 0%, #C8102E 100%); }
        .usa-card { background: linear-gradient(135deg, #3C3B6E 0%, #B22234 100%); }
        .uk-card { background: linear-gradient(135deg, #012169 0%, #C8102E 100%); }
        .australia-card { background: linear-gradient(135deg, #00008B 0%, #FFD700 100%); }
        .japan-card { background: linear-gradient(135deg, #BC002D 0%, #FFFFFF 100%); }
        .singapore-card { background: linear-gradient(135deg, #FF0000 0%, #FFFFFF 100%); }
        .uae-card { background: linear-gradient(135deg, #CE1126 0%, #007A5E 50%, #000000 100%); }
        .germany-card { background: linear-gradient(135deg, #000000 0%, #DD0000 50%, #FFCE00 100%); }
        .france-card { background: linear-gradient(135deg, #002395 0%, #FFFFFF 50%, #ED2939 100%); }
        .spain-card { background: linear-gradient(135deg, #FFC400 0%, #FFC400 50%, #C60B1E 100%); }
        .mexico-card { background: linear-gradient(135deg, #CE3126 0%, #FFFFFF 50%, #007236 100%); }
        .brazil-card { background: linear-gradient(135deg, #009739 0%, #FFCC00 50%, #002776 100%); }
        .nz-card { background: linear-gradient(135deg, #00247D 0%, #CC142B 100%); }
        .hongkong-card { background: linear-gradient(135deg, #DE2910 0%, #FFFFFF 100%); }
        .thailand-card { background: linear-gradient(135deg, #A4161A 0%, #FFFFFF 50%, #A4161A 100%); }
        .malaysia-card { background: linear-gradient(135deg, #007A5E 0%, #FFCC00 100%); }
        .southkorea-card { background: linear-gradient(135deg, #C60C30 0%, #FFFFFF 50%, #003478 100%); }
        .indonesia-card { background: linear-gradient(135deg, #FF0000 0%, #FFFFFF 50%, #FF0000 100%); }
    </style>
    """, unsafe_allow_html=True)
    
    # Logout button in top right
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("🚪", key="logout_btn", help="Logout"):
            AuthManager.logout()
            st.rerun()
    
    # Main content
    st.markdown('<div class="country-page">', unsafe_allow_html=True)
    
    # Header
    st.markdown(f"""
    <div class="page-header">
        <h1>⚖️ LexiVoice</h1>
        <p>Welcome, <strong>{st.session_state.user['name']}</strong>!</p>
        <p class="page-subtitle">Select your country to access legal information</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Countries data
    countries = [
        {'code': 'india', 'flag': '🇮🇳', 'name': 'India', 'description': 'Immigration, labor & civil law', 'card_class': 'india-card', 'laws': '10+'},
        {'code': 'canada', 'flag': '🇨🇦', 'name': 'Canada', 'description': 'Immigration, labor & consumer law', 'card_class': 'canada-card', 'laws': '10+'},
        {'code': 'usa', 'flag': '🇺🇸', 'name': 'USA', 'description': 'Federal employment & consumer law', 'card_class': 'usa-card', 'laws': '27+'},
        {'code': 'uk', 'flag': '🇬🇧', 'name': 'UK', 'description': 'Employment & immigration law', 'card_class': 'uk-card', 'laws': '8+'},
        {'code': 'australia', 'flag': '🇦🇺', 'name': 'Australia', 'description': 'Employment & visa law', 'card_class': 'australia-card', 'laws': '9+'},
        {'code': 'japan', 'flag': '🇯🇵', 'name': 'Japan', 'description': 'Labor & visa regulations', 'card_class': 'japan-card', 'laws': '7+'},
        {'code': 'singapore', 'flag': '🇸🇬', 'name': 'Singapore', 'description': 'Employment & immigration law', 'card_class': 'singapore-card', 'laws': '8+'},
        {'code': 'uae', 'flag': '🇦🇪', 'name': 'UAE', 'description': 'Labor & residency laws', 'card_class': 'uae-card', 'laws': '9+'},
        {'code': 'germany', 'flag': '🇩🇪', 'name': 'Germany', 'description': 'Employment & immigration law', 'card_class': 'germany-card', 'laws': '8+'},
        {'code': 'france', 'flag': '🇫🇷', 'name': 'France', 'description': 'Labor & employment regulations', 'card_class': 'france-card', 'laws': '7+'},
        {'code': 'spain', 'flag': '🇪🇸', 'name': 'Spain', 'description': 'Employment & labor law', 'card_class': 'spain-card', 'laws': '7+'},
        {'code': 'mexico', 'flag': '🇲🇽', 'name': 'Mexico', 'description': 'Labor & employment law', 'card_class': 'mexico-card', 'laws': '6+'},
        {'code': 'brazil', 'flag': '🇧🇷', 'name': 'Brazil', 'description': 'Labor & immigration law', 'card_class': 'brazil-card', 'laws': '8+'},
        {'code': 'newzealand', 'flag': '🇳🇿', 'name': 'New Zealand', 'description': 'Employment & visa information', 'card_class': 'nz-card', 'laws': '7+'},
        {'code': 'hongkong', 'flag': '🇭🇰', 'name': 'Hong Kong', 'description': 'Employment & immigration law', 'card_class': 'hongkong-card', 'laws': '8+'},
        {'code': 'thailand', 'flag': '🇹🇭', 'name': 'Thailand', 'description': 'Labor & work permit regulations', 'card_class': 'thailand-card', 'laws': '6+'},
        {'code': 'malaysia', 'flag': '🇲🇾', 'name': 'Malaysia', 'description': 'Employment & immigration law', 'card_class': 'malaysia-card', 'laws': '7+'},
        {'code': 'southkorea', 'flag': '🇰🇷', 'name': 'South Korea', 'description': 'Labor & employment law', 'card_class': 'southkorea-card', 'laws': '7+'},
        {'code': 'indonesia', 'flag': '🇮🇩', 'name': 'Indonesia', 'description': 'Labor & employment law', 'card_class': 'indonesia-card', 'laws': '6+'},
    ]
    
    # Create grid layout
    st.markdown('<div class="country-grid">', unsafe_allow_html=True)
    
    cols = st.columns(4)
    for idx, country in enumerate(countries):
        with cols[idx % 4]:
            # Make entire card clickable
            if st.button(
                label=f"{country['flag']} {country['name']}",
                key=f"country_{country['code']}",
                use_container_width=True
            ):
                st.session_state.selected_country = country['code']
                try:
                    AuthManager.update_user_country(
                        st.session_state.user['email'],
                        country['code']
                    )
                except:
                    pass
                st.success(f"✅ {country['name']} selected!")
                st.rerun()
            
            # Display card HTML
            st.markdown(f"""
            <div class="country-card {country['card_class']}">
                <div class="country-card-content">
                    <span class="country-flag">{country['flag']}</span>
                    <div class="country-name">{country['name']}</div>
                    <div class="country-description">{country['description']}</div>
                    <div class="country-features">
                        <span class="feature-badge">📚 {country['laws']} docs</span>
                        <span class="feature-badge">⚡ Instant</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div></div>', unsafe_allow_html=True)