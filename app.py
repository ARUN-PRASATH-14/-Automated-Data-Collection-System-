import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_supabase_client
from run_pipeline import run_all_sources
from utils.llm import rewrite_article
from config import logger

# Initialize Supabase client
supabase = get_supabase_client()

# ----------------------------------
# Page Configuration
# ----------------------------------
st.set_page_config(
    page_title="AI & Startup Content Collector",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------
# Premium Visual Style (Vanilla CSS Injection)
# ----------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Modern typography */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Metrics display styling */
    div[data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.1);
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.01);
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.3);
        box-shadow: 0 8px 16px rgba(0,0,0,0.04);
    }
    
    /* Article visual container */
    .article-card {
        background: rgba(128, 128, 128, 0.02);
        border: 1px solid rgba(128, 128, 128, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.01);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .article-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 12px 24px rgba(59, 130, 246, 0.06);
        transform: translateY(-2px);
    }
    
    /* Source Badges */
    .source-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 100px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-right: 10px;
    }
    .badge-nvidia { background-color: rgba(118, 185, 0, 0.12); color: #76B900; border: 1px solid rgba(118, 185, 0, 0.2); }
    .badge-anthropic { background-color: rgba(217, 119, 6, 0.12); color: #D97706; border: 1px solid rgba(217, 119, 6, 0.2); }
    .badge-hackernews { background-color: rgba(255, 102, 0, 0.12); color: #FF6600; border: 1px solid rgba(255, 102, 0, 0.2); }
    .badge-unknown { background-color: rgba(107, 114, 128, 0.12); color: #6B7280; border: 1px solid rgba(107, 114, 128, 0.2); }
    
    /* Interactive design enhancements */
    a.article-link {
        text-decoration: none;
        font-weight: 600;
        color: #3b82f6;
        transition: color 0.2s;
    }
    a.article-link:hover {
        color: #1d4ed8;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------
# Sidebar & Pipeline Runner
# ----------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/news.png", width=80)
    st.title("Control Panel")
    st.write("Manage pipeline triggers and view filters.")
    
    st.divider()
    
    # Run collector pipeline
    if st.button("🔄 Trigger Content Fetch", use_container_width=True):
        with st.spinner("Scraping AI feeds & rewriting..."):
            try:
                run_all_sources()
                st.success("Refreshed content successfully!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Pipeline running error: {e}")
                
    st.divider()
    
    # Query Controls
    st.subheader("Filters")
    search_query = st.text_input("🔍 Search Titles", placeholder="Enter keywords...")
    
    source_list = ["All", "NVIDIA", "Anthropic", "HackerNews"]
    source_filter = st.selectbox("🏢 Select Source", source_list)
    
    sort_order = st.selectbox("📅 Sort Order", ["Newest First", "Oldest First"])
    
    st.divider()
    st.caption("AI & Startup Content Collector v2.0 • Premium Dashboard Layout")

# ----------------------------------
# Header Section
# ----------------------------------
st.title("📰 AI & Startup Content Collector")
st.markdown("An automated pipeline aggregating, rewriting, and visualising multi-source artificial intelligence insights.")
st.divider()

# ----------------------------------
# Optimized Supabase Query & Load
# ----------------------------------
@st.cache_data(ttl=120)  # Cache data for 2 minutes to reduce Supabase query loads
def load_articles():
    if not supabase:
        return []
    try:
        # Optimization: limit download load size to 100 rows to ensure snappy dashboard page renders
        response = (
            supabase.table("articles")
            .select("id, title, url, source, published_at, rewritten_article, original_content")
            .order("published_at", desc=True)
            .limit(100)
            .execute()
        )
        return response.data
    except Exception as e:
        logger.error(f"Supabase load error: {e}")
        return []

articles_data = load_articles()

if not articles_data:
    st.warning("⚠️ No records loaded. Please verify your Supabase database connections and hit 'Trigger Content Fetch'.")
    st.stop()

# Load into DataFrame for filter processing
df = pd.DataFrame(articles_data)

# Apply filter: Source
if source_filter != "All":
    df = df[df["source"] == source_filter]

# Apply filter: Search Query
if search_query:
    df = df[df["title"].str.contains(search_query, case=False, na=False)]

# Apply filter: Sort Order
if sort_order == "Newest First":
    df = df.sort_values(by="published_at", ascending=False)
else:
    df = df.sort_values(by="published_at", ascending=True)

# ----------------------------------
# Metric KPI Grid
# ----------------------------------
st.subheader("📊 Dashboard Metrics")
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("📰 Matches", len(df))
with m2:
    st.metric("🏢 Active Sources", df["source"].nunique())
with m3:
    st.metric("⚡ Rewritten Articles", df["rewritten_article"].notna().sum())
with m4:
    # Count of missing/failed rewrites
    missing_rewrites = df["rewritten_article"].isna().sum()
    st.metric("🚨 Rewrites Missing", missing_rewrites, delta=int(missing_rewrites), delta_color="inverse" if missing_rewrites > 0 else "normal")

# ----------------------------------
# Analytics: Charts
# ----------------------------------
col_chart, col_empty = st.columns([2, 1])
with col_chart:
    st.subheader("📈 Article Distribution by Publisher")
    dist = df["source"].value_counts()
    st.bar_chart(dist, height=200)

st.divider()

# ----------------------------------
# Main Article Feed
# ----------------------------------
st.subheader("📰 Latest Insights Feed")

if df.empty:
    st.info("No articles match your active search filter settings.")
else:
    for idx, row in df.iterrows():
        # Map source labels to HSL colors for premium CSS design
        source_class = "badge-unknown"
        s_lower = str(row['source']).lower()
        if "nvidia" in s_lower:
            source_class = "badge-nvidia"
        elif "anthropic" in s_lower:
            source_class = "badge-anthropic"
        elif "hacker" in s_lower:
            source_class = "badge-hackernews"

        # Format ISO string nicely
        pub_str = row.get("published_at")
        if pub_str:
            try:
                dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                pub_str = dt.strftime("%B %d, %Y - %I:%M %p UTC")
            except Exception:
                pass
        else:
            pub_str = "Unknown Date"

        # Render custom article container structure
        st.markdown(f"""
        <div class="article-card">
            <div style="margin-bottom: 12px;">
                <span class="source-badge {source_class}">{row['source']}</span>
                <span style="font-size: 0.82rem; color: #888888;">📅 {pub_str}</span>
            </div>
            <h3 style="margin: 0 0 10px 0; font-size: 1.4rem; font-weight: 700;">{row['title']}</h3>
            <p style="margin-bottom: 15px;"><a class="article-link" href="{row['url']}" target="_blank">🔗 Read Original Article</a></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs for clean structured layout
        t_rewritten, t_original = st.tabs(["✨ AI Rewritten Article", "📄 Original Scraped Content"])
        
        with t_rewritten:
            rewritten_text = row.get("rewritten_article")
            if rewritten_text:
                st.write(rewritten_text)
            else:
                st.info("💡 An AI rewrite is not available for this article.")
                
                # In-app on-demand manual trigger
                btn_key = f"regenerate_btn_{row['id']}"
                if st.button("⚡ Generate AI Summary", key=btn_key):
                    with st.spinner("Calling Hugging Face Inference..."):
                        original_text = row.get("original_content")
                        if not original_text:
                            st.error("Cannot regenerate: original content is missing.")
                        else:
                            # Invoke live rewrite utility
                            new_rewrite = rewrite_article(original_text)
                            if new_rewrite:
                                try:
                                    # Save to Supabase
                                    supabase.table("articles").update({"rewritten_article": new_rewrite}).eq("id", row['id']).execute()
                                    st.success("Rewrite generated successfully!")
                                    st.cache_data.clear()  # Clear cache to force refresh from DB
                                    st.rerun()
                                except Exception as db_err:
                                    st.error(f"Failed to update Supabase record: {db_err}")
                            else:
                                st.error("Inference failed. HF limits may be exhausted. See terminal logs.")
                                
        with t_original:
            orig_text = row.get("original_content")
            if orig_text:
                with st.expander("Show Raw Scraped Text"):
                    st.text(orig_text)
            else:
                st.warning("Original text content is empty.")
                
        st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
