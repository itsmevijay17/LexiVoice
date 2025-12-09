"""
Statistics Page - View system usage and performance metrics.
"""
import streamlit as st
import pandas as pd


def show():
    """Display statistics dashboard."""
    
    st.markdown("### 📊 System Statistics")
    
    # Fetch stats from backend
    with st.spinner("Loading statistics..."):
        stats = st.session_state.api_client.get_stats()
    
    if 'error' in stats:
        st.error(f"❌ Could not load statistics: {stats['error']}")
        return
    
    # Overall metrics
    st.markdown("#### 📈 Overall Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Queries",
            value=stats.get('total_queries', 0)
        )
    
    with col2:
        feedback_data = stats.get('feedback', {})
        st.metric(
            label="Total Feedback",
            value=feedback_data.get('total_feedback', 0)
        )
    
    with col3:
        st.metric(
            label="Average Rating",
            value=f"{feedback_data.get('average_rating', 0):.2f} / 5.0"
        )
    
    # Queries by country
    st.markdown("---")
    st.markdown("#### 🌍 Queries by Country")
    
    queries_by_country = stats.get('queries_by_country', [])
    
    if queries_by_country:
        df_country = pd.DataFrame(queries_by_country)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.bar_chart(
                df_country.set_index('country')['count'],
                use_container_width=True
            )
        
        with col2:
            st.dataframe(
                df_country,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("No query data available yet.")
    
    # Feedback distribution
    st.markdown("---")
    st.markdown("#### ⭐ Feedback Rating Distribution")
    
    rating_dist = feedback_data.get('rating_distribution', {})
    
    if rating_dist:
        # Convert to DataFrame
        df_ratings = pd.DataFrame([
            {'Rating': f"{rating} ⭐", 'Count': count}
            for rating, count in sorted(rating_dist.items())
        ])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.bar_chart(
                df_ratings.set_index('Rating')['Count'],
                use_container_width=True
            )
        
        with col2:
            st.dataframe(
                df_ratings,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("No feedback data available yet.")
    
    # Refresh button
    st.markdown("---")
    if st.button("🔄 Refresh Statistics", use_container_width=True):
        st.rerun()