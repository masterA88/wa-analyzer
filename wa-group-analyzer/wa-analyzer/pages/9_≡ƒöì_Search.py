"""
🔍 Search Messages
====================
Full-text search with user and date filters.
"""

import streamlit as st
import pandas as pd
from utils.parser import search_messages
from utils.helpers import date_range_filter, export_buttons

st.set_page_config(page_title="Search", page_icon="🔍", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("⬅️ Please upload a chat file on the main page first.")
    st.stop()

df = st.session_state.df.copy()

st.markdown("## 🔍 Search Messages")

# ── SEARCH INPUT ─────────────────────────────────────────────────────────────
query = st.text_input("🔎 Search query:", placeholder="Type keyword, phrase, or URL...",
                        key="search_query")

# ── FILTERS ──────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    users = sorted(df[~df['is_system']]['user'].unique())
    user_filter = st.multiselect("Filter by user:", users, key="search_users")

with col2:
    start = st.date_input("From:", value=df['date'].min(),
                            min_value=df['date'].min(), max_value=df['date'].max(),
                            key="search_start")

with col3:
    end = st.date_input("To:", value=df['date'].max(),
                          min_value=df['date'].min(), max_value=df['date'].max(),
                          key="search_end")

# ── SEARCH ───────────────────────────────────────────────────────────────────
if query:
    results = search_messages(
        df, query,
        user_filter=user_filter if user_filter else None,
        date_range=(start, end)
    )
    results_user = results[~results['is_system']]

    st.markdown(f"### Found **{len(results_user):,}** results for \"{query}\"")

    if not results_user.empty:
        # Results per user
        user_dist = results_user['user'].value_counts().head(10)
        st.markdown("**Results by user:** " +
                    ", ".join(f"{u} ({c})" for u, c in user_dist.items()))

        st.divider()

        # Show results
        display_df = results_user[['date', 'time', 'user', 'message']].copy()
        display_df['date'] = display_df['date'].astype(str)
        display_df['time'] = display_df['time'].astype(str)

        # Highlight query in messages
        def highlight_msg(msg):
            import re
            highlighted = re.sub(
                f'({re.escape(query)})',
                r'**\1**',
                msg,
                flags=re.IGNORECASE
            )
            return highlighted[:300] + "..." if len(highlighted) > 300 else highlighted

        display_df['message'] = display_df['message'].apply(highlight_msg)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'date': 'Date',
                'time': 'Time',
                'user': 'User',
                'message': st.column_config.TextColumn('Message', width="large"),
            },
            height=600,
        )

        # Export
        st.divider()
        with st.expander("📥 Export Search Results"):
            raw = results_user[['date', 'time', 'user', 'message']].copy()
            export_buttons(raw, "search_export", f"search_{query}")

    else:
        st.info("No messages found matching your search criteria.")
else:
    st.markdown("""
    <div style="text-align: center; padding: 40px; color: #64748b;">
        <div style="font-size: 48px; margin-bottom: 12px;">🔍</div>
        <p>Type a keyword above to search through all messages</p>
        <p style="font-size: 12px;">
            Try: <code>SQL</code> · <code>loker</code> · <code>interview</code> ·
            <code>linkedin.com</code> · <code>python</code>
        </p>
    </div>
    """, unsafe_allow_html=True)
