"""
WhatsApp Group Analyzer
=======================
Main entry point — file upload, parsing, and navigation.
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from utils.parser import extract_text_from_upload, parse_chat

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="WA Group Analyzer",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load custom CSS
css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


# ── SESSION STATE ────────────────────────────────────────────────────────────

def init_session():
    """Initialize session state variables."""
    defaults = {
        'df': None,
        'raw_text': None,
        'file_name': None,
        'parsed': False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session()


# ── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0 20px;">
        <div style="
            display: inline-flex; align-items: center; justify-content: center;
            width: 52px; height: 52px; border-radius: 14px;
            background: linear-gradient(135deg, #10b981 0%, #0ea5e9 100%);
            font-size: 24px; font-weight: 800; color: white;
            margin-bottom: 8px;
        ">💬</div>
        <h2 style="margin: 0; font-size: 18px; color: #f1f5f9;">WA Analyzer</h2>
        <p style="margin: 4px 0 0; font-size: 11px; color: #64748b;">
            Community Intelligence Tool
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # File Upload
    st.markdown("##### 📤 Upload Chat Export")
    uploaded_file = st.file_uploader(
        "Drop your WhatsApp export here",
        type=['txt', 'zip'],
        help="Export from WhatsApp: Chat → More → Export Chat → Without Media",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        # Detect new file by name + size (handles same filename from different groups)
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get('file_id') != file_id:
            with st.spinner("🔄 Parsing chat data..."):
                try:
                    raw_text = extract_text_from_upload(uploaded_file)
                    df = parse_chat(raw_text)

                    if df.empty:
                        st.error("❌ Could not parse any messages. Check the file format.")
                    else:
                        st.session_state.df = df
                        st.session_state.raw_text = raw_text
                        st.session_state.file_name = uploaded_file.name
                        st.session_state.file_id = file_id
                        st.session_state.parsed = True
                        st.success(f"✅ Parsed **{len(df):,}** messages from **{df['user'].nunique()}** users")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Show data summary in sidebar
    if st.session_state.parsed and st.session_state.df is not None:
        df = st.session_state.df

        st.divider()
        st.markdown("##### 📊 Data Summary")

        st.markdown(f"""
        <div style="font-size: 12px; color: #94a3b8; line-height: 2;">
            📁 <b style="color:#f1f5f9;">{st.session_state.file_name}</b><br>
            💬 <b style="color:#10b981;">{len(df):,}</b> messages<br>
            👥 <b style="color:#10b981;">{df[~df['is_system']]['user'].nunique()}</b> users<br>
            📅 {df['date'].min()} → {df['date'].max()}<br>
            🖼️ <b style="color:#10b981;">{df['is_media'].sum():,}</b> media files
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown("##### 🧭 Navigation")
        st.markdown("""
        <div style="font-size: 12px; color: #64748b; line-height: 2.2;">
        Use the <b style="color: #94a3b8;">sidebar pages</b> above to explore:<br>
        📊 Overview Dashboard<br>
        🏆 User Leaderboard<br>
        📇 Member Directory<br>
        ⏰ Temporal Analytics<br>
        💬 Topics & Content<br>
        😊 Emoji & Sentiment<br>
        🕸️ Network Graph<br>
        🔍 Search Messages<br>
        📥 Export Center
        </div>
        """, unsafe_allow_html=True)
    else:
        st.divider()
        st.info("👆 Upload a file to get started")


# ── MAIN CONTENT ─────────────────────────────────────────────────────────────

if not st.session_state.parsed:
    # Landing page
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <div style="font-size: 64px; margin-bottom: 16px;">💬</div>
        <h1 style="font-size: 36px; font-weight: 800; margin-bottom: 8px;">
            WhatsApp Group Analyzer
        </h1>
        <p style="font-size: 16px; color: #64748b; max-width: 500px; margin: 0 auto 40px;">
            Transform your WhatsApp chat exports into actionable community intelligence.
            Upload a <code>.txt</code> or <code>.zip</code> file to get started.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature preview cards
    col1, col2, col3 = st.columns(3)
    features = [
        ("📊", "Activity Dashboard", "See who's most active, peak hours, daily trends"),
        ("📇", "Member Directory", "Auto-extract names, locations, LinkedIn profiles"),
        ("💬", "Topic Analysis", "Word clouds, keyword tracking, content insights"),
        ("😊", "Emoji Analytics", "Top emojis, sentiment pulse, mood tracking"),
        ("🕸️", "Social Network", "Visualize who interacts with whom"),
        ("📥", "Export Everything", "CSV, Excel, PNG — download any data or chart"),
    ]

    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #111827 0%, #1e293b 100%);
                border: 1px solid #1e3a5f; border-radius: 12px;
                padding: 24px; text-align: center; margin-bottom: 12px;
                min-height: 140px;
            ">
                <div style="font-size: 28px; margin-bottom: 8px;">{icon}</div>
                <div style="font-size: 15px; font-weight: 700; color: #f1f5f9; margin-bottom: 4px;">{title}</div>
                <div style="font-size: 12px; color: #64748b;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin-top: 30px;">
        <p style="font-size: 13px; color: #475569;">
            📤 Upload your WhatsApp chat export from the sidebar to begin analysis
        </p>
        <p style="font-size: 11px; color: #334155; margin-top: 8px;">
            How to export: Open WhatsApp → Group Chat → ⋮ More → Export Chat → Without Media
        </p>
    </div>
    """, unsafe_allow_html=True)

else:
    # Post-upload: show quick overview
    df = st.session_state.df

    st.markdown("## 📊 Quick Overview")
    st.markdown(f"*{st.session_state.file_name}* — **{len(df):,}** messages "
                f"from **{df[~df['is_system']]['user'].nunique()}** users "
                f"({df['date'].min()} to {df['date'].max()})")

    # KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)

    user_msgs = df[~df['is_system']]
    total_days = (df['date'].max() - df['date'].min()).days + 1

    with col1:
        st.metric("💬 Messages", f"{len(user_msgs):,}")
    with col2:
        st.metric("👥 Users", f"{user_msgs['user'].nunique()}")
    with col3:
        st.metric("📅 Days Active", f"{total_days}")
    with col4:
        st.metric("📊 Avg/Day", f"{len(user_msgs) / max(total_days, 1):.0f}")
    with col5:
        st.metric("🖼️ Media", f"{df['is_media'].sum():,}")

    st.divider()
    st.markdown("### 👈 Navigate using the sidebar pages to explore detailed analytics")

    # Quick preview: top 5 users
    top_users = user_msgs['user'].value_counts().head(5)
    st.markdown("#### 🏆 Top 5 Active Users")
    for i, (user, count) in enumerate(top_users.items()):
        pct = count / len(user_msgs) * 100
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 12px; padding: 6px 0;">
            <span style="font-weight: 700; color: {'#fbbf24' if i < 3 else '#64748b'}; width: 24px;">#{i+1}</span>
            <span style="flex: 1; color: #e2e8f0;">{user}</span>
            <div style="
                height: 8px; width: {pct * 3}px; border-radius: 4px;
                background: linear-gradient(90deg, #10b981, {'#0ea5e9' if i < 3 else '#334155'});
            "></div>
            <span style="color: #94a3b8; font-size: 13px; width: 80px; text-align: right;">
                {count:,} ({pct:.1f}%)
            </span>
        </div>
        """, unsafe_allow_html=True)
