# ui/streamlit_app.py
import sys
import os
import time
import streamlit as st
import yaml
from dotenv import load_dotenv
from typing import List, Optional

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraping.rss_scraper import fetch_articles, get_all_available_sources
from chains.filter_chain import classify_and_score_articles
from delivery.emailer import send_email
from app import filter_and_rank_articles

# Load environment variables
load_dotenv()

# Load config
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(base_dir, "config.yaml")
with open(config_path, encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Enhanced page config
st.set_page_config(
    page_title="AI News Filter", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (keep the same CSS as before)
st.markdown("""
<style>
    /* ... (keep all existing CSS styles) ... */
</style>
""", unsafe_allow_html=True)

# Custom header
st.markdown("""
<div class="custom-header">
    <h1>🧠 AI News Intelligence</h1>
    <p>Advanced news classification and delivery platform powered by artificial intelligence</p>
</div>
""", unsafe_allow_html=True)

# Sidebar UI with source selection
with st.sidebar:
    st.markdown('<div class="section-header">🔍 Configuration</div>', unsafe_allow_html=True)
    
    topic = st.selectbox("Select Topic", [
        "education", "technology", "science", "health", "business", "finance", "environment"
    ], index=0)

    col1, col2 = st.columns(2)
    with col1:
        region = st.radio("Region", ["India", "Global"], index=0)
    with col2:
        content_type = st.radio("Content", ["General", "Sensitive"], index=0)
    
    num_articles = st.slider("Max Articles", 5, 100, 10, 5)

    st.markdown('<div class="section-header">📰 News Sources</div>', unsafe_allow_html=True)
    
    # Get available sources for the selected topic/region
    all_sources_data = get_all_available_sources()
    topic_sources = all_sources_data.get(topic, {}).get(region.lower(), [])
    general_sources = all_sources_data.get("general", [])
    all_sources = topic_sources + general_sources
    
    # Create multiselect with all available sources
    selected_sources = st.multiselect(
        "Select News Sources",
        options=[source["name"] for source in all_sources],
        default=[source["name"] for source in all_sources[:3]],  # Default to first 3 sources
        help="Choose which news sources to include in your feed"
    )
    
    # Button to select/deselect all
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Select All"):
            selected_sources = [source["name"] for source in all_sources]
    with col2:
        if st.button("Deselect All"):
            selected_sources = []
    
    st.markdown('<div class="section-header">📩 Email Delivery</div>', unsafe_allow_html=True)
    recipient_input = st.text_input("Recipients (comma-separated):", placeholder="email1@example.com, email2@example.com")
    recipient_emails = [e.strip() for e in recipient_input.split(",") if e.strip()]
    
    if recipient_emails:
        st.success(f"✅ {len(recipient_emails)} recipient(s) configured")

    st.markdown('<div class="section-header">⚙️ Advanced Settings</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        batch_size = st.slider("Batch Size", 5, 20, 10)
    with col2:
        min_score = st.slider("Min Score", 0, 100, 30)
    
    use_prefilter = st.checkbox("Use Keyword Pre-Filter", True)

    st.markdown("---")
    submit = st.button("🚀 Start Analysis")

# Show available sources in an expander
with st.sidebar:
    if st.checkbox("Show all available sources"):
        st.markdown('<div class="section-header">📋 All Sources</div>', unsafe_allow_html=True)
        for topic_name, regions in all_sources_data.items():
            if topic_name == "general":
                continue
            with st.expander(f"{topic_name.title()} Sources"):
                for region_name, sources in regions.items():
                    st.markdown(f"**{region_name.title()}**")
                    for source in sources:
                        st.markdown(f"- {source['name']}")
        
        with st.expander("General Sources"):
            for source in all_sources_data.get("general", []):
                st.markdown(f"- {source['name']}")

# Main content area
if submit:
    start_time = time.time()
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        st.markdown(f'<div class="status-success">🔄 Processing {topic.title()} ({region})</div>', unsafe_allow_html=True)

    status_container = st.container()
    progress_container = st.container()
    
    with progress_container:
        progress = st.progress(0)
        status = st.empty()

    # Step 1: Fetch
    with status_container:
        st.markdown("### 📡 Phase 1: Article Fetching")
        status.text("🔍 Searching for relevant articles...")
    
    articles = fetch_articles(topic, region.lower(), selected_sources if selected_sources else None)
    total_fetched = len(articles)
    progress.progress(10)
    
    if total_fetched > 0:
        st.markdown(f'<div class="status-success">✅ Successfully fetched {total_fetched} articles</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-error">❌ No articles found. Try a different topic or region.</div>', unsafe_allow_html=True)
        st.stop()

    # Step 2: Classify
    with status_container:
        st.markdown("### 🧠 Phase 2: AI Classification")
        status.text("🤖 Analyzing articles with AI classifier...")
    
    scored = classify_and_score_articles(
        articles,
        batch_size=batch_size,
        use_prefilter=use_prefilter,
        min_score=min_score,
        topic=topic
    )
    progress.progress(60)
    
    if len(scored) > 0:
        st.markdown(f'<div class="status-success">✅ {len(scored)} articles passed classification filters</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-warning">⚠️ No articles passed classification filters</div>', unsafe_allow_html=True)
        st.stop()

    # Step 3: Filter
    with status_container:
        st.markdown("### 📄 Phase 3: Final Filtering")
        status.text("🔧 Applying user preferences...")
    
    user_filter = {
        "topic": topic,
        "region": region,
        "content_type": content_type
    }
    final = filter_and_rank_articles(scored, user_filter, max_articles=num_articles)
    progress.progress(85)
    
    st.markdown(f'<div class="status-success">✅ {len(final)} articles match your preferences</div>', unsafe_allow_html=True)

    # Step 4: Display Results
    with status_container:
        st.markdown("### 📊 Results")
        status.text("📤 Preparing results...")

    if final:
        st.markdown("#### 📰 Filtered Articles")

        for idx, article in enumerate(final, 1):
            classification = article.get("classification", {})
            region_val = classification.get("region", "Unknown")
            source_name = article.get("source", "Unknown")

            with st.expander(f"{idx}. {article['title']}", expanded=False):
                st.markdown(f"🔗 **[Read Full Article]({article['link']})**")
                if article.get("summary"):
                    st.markdown(f"📝 **Summary:** {article['summary']}")
                st.caption(f"🌐 **Source:** {source_name} | 🗺️ **Region:** {region_val}")

        # Email functionality
        if recipient_emails:
            try:
                email_articles = [{
                    'title': a['title'],
                    'link': a['link'],
                    'summary': a.get('summary', ''),
                    'image': a.get('image', '')
                } for a in final]

                send_email(email_articles, topic=topic, recipients=recipient_emails)
                st.markdown(f'<div class="status-success">📧 Email sent successfully to {len(recipient_emails)} recipients</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="status-error">❌ Email sending failed: {e}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-warning">⚠️ No articles matched your criteria</div>', unsafe_allow_html=True)
        
    progress.progress(100)
    status.empty()

    # Enhanced Summary Metrics
    st.markdown("---")
    st.markdown("### 📊 Performance Analytics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    duration = time.time() - start_time
    efficiency = (len(final) / max(total_fetched, 1)) * 100

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_fetched}</div>
            <div class="metric-label">Fetched</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(scored)}</div>
            <div class="metric-label">Classified</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(final)}</div>
            <div class="metric-label">Final</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{duration:.1f}s</div>
            <div class="metric-label">Duration</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{efficiency:.0f}%</div>
            <div class="metric-label">Efficiency</div>
        </div>
        """, unsafe_allow_html=True)

    # Enhanced sidebar summary
    with st.sidebar:
        st.markdown('<div class="section-header">📋 Session Summary</div>', unsafe_allow_html=True)
        st.markdown(f"""
        **🎯 Topic:** {topic.title()}  
        **🌍 Region:** {region}  
        **📄 Content:** {content_type}  
        **📊 Max Articles:** {num_articles}  
        **⚙️ Batch Size:** {batch_size}  
        **🎚️ Min Score:** {min_score}  
        **⏱️ Duration:** {duration:.1f}s  
        **📰 Sources Used:** {len(selected_sources) if selected_sources else 'All'}
        """)
        
        if recipient_emails:
            st.markdown(f"**📧 Recipients:** {len(recipient_emails)}")
            for email in recipient_emails:
                st.markdown(f"• {email}")

# Footer with branding
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 2rem 0;">
    <p><strong>AI News Intelligence Platform</strong> • Powered by Advanced Machine Learning</p>
    <p style="font-size: 0.9rem;">Delivering personalized, relevant news content with AI precision</p>
</div>
""", unsafe_allow_html=True)