"""
😊 Emoji & Sentiment Analytics
================================
Emoji usage, sentiment indicators, and group mood tracking.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
from utils.parser import get_emoji_stats, extract_emojis_from_text
from utils.helpers import apply_chart_theme, CHART_COLORS, date_range_filter, export_buttons

st.set_page_config(page_title="Emoji & Sentiment", page_icon="😊", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("⬅️ Please upload a chat file on the main page first.")
    st.stop()

df = st.session_state.df.copy()

st.markdown("## 😊 Emoji & Sentiment Analytics")

with st.expander("🗓️ Filter by Date Range", expanded=False):
    df, _, _ = date_range_filter(df, "emoji")

user_msgs = df[~df['is_system'] & (df['user'] != 'system')]

# ── EMOJI STATS ──────────────────────────────────────────────────────────────
@st.cache_data
def compute_emoji_stats(_df):
    return get_emoji_stats(_df)

emoji_counter, user_emoji = compute_emoji_stats(user_msgs)

total_emojis = sum(emoji_counter.values())
unique_emojis = len(emoji_counter)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🎨 Total Emojis Used", f"{total_emojis:,}")
with col2:
    st.metric("✨ Unique Emojis", f"{unique_emojis}")
with col3:
    st.metric("📊 Avg per Message", f"{total_emojis / max(len(user_msgs), 1):.2f}")

st.divider()

# ── TOP EMOJIS ───────────────────────────────────────────────────────────────
st.markdown("### 🏆 Top Emojis")

top_n_emoji = st.slider("Show top:", 10, 50, 20, key="emoji_top_n")
top_emojis = emoji_counter.most_common(top_n_emoji)

if top_emojis:
    emoji_df = pd.DataFrame(top_emojis, columns=['Emoji', 'Count'])

    fig = px.bar(emoji_df, x='Emoji', y='Count',
                 color='Count',
                 color_continuous_scale=['#1e293b', '#f59e0b'],
                 text='Count')
    fig.update_traces(texttemplate='%{text:,}', textposition='outside', textfont_size=10)
    apply_chart_theme(fig)
    fig.update_layout(height=400, xaxis_title="", yaxis_title="Usage Count",
                      coloraxis_showscale=False,
                      xaxis=dict(tickfont_size=18))
    st.plotly_chart(fig, use_container_width=True)

    # Big emoji display
    st.markdown("#### Most Used")
    cols = st.columns(min(10, len(top_emojis)))
    for i, (em, count) in enumerate(top_emojis[:10]):
        with cols[i]:
            st.markdown(f"""
            <div style="text-align: center; padding: 8px;">
                <div style="font-size: 32px;">{em}</div>
                <div style="font-size: 12px; color: #94a3b8; font-weight: 600;">{count:,}</div>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ── PER-USER EMOJI ───────────────────────────────────────────────────────────
st.markdown("### 👤 Per-User Emoji Profile")

top_users = user_msgs['user'].value_counts().head(20).index.tolist()
selected_user = st.selectbox("Select user:", top_users, key="emoji_user_select")

if selected_user in user_emoji and user_emoji[selected_user]:
    user_top = user_emoji[selected_user].most_common(15)
    u_emoji_df = pd.DataFrame(user_top, columns=['Emoji', 'Count'])

    col1, col2 = st.columns([2, 1])
    with col1:
        fig = px.bar(u_emoji_df, x='Emoji', y='Count',
                     color_discrete_sequence=['#10b981'],
                     text='Count')
        fig.update_traces(textposition='outside', textfont_size=10)
        apply_chart_theme(fig)
        fig.update_layout(height=300, xaxis=dict(tickfont_size=16))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        total_user_emoji = sum(user_emoji[selected_user].values())
        st.markdown(f"""
        **{selected_user}**
        - Total emojis: **{total_user_emoji:,}**
        - Unique emojis: **{len(user_emoji[selected_user])}**
        - Favorite: **{user_top[0][0]}** ({user_top[0][1]:,} times)
        """)
else:
    st.info(f"No emoji data for {selected_user}")

st.divider()

# ── SENTIMENT INDICATORS ────────────────────────────────────────────────────
st.markdown("### 🌡️ Group Mood Indicators")

positive_words = ['keren', 'mantap', 'bagus', 'hebat', 'thanks', 'terima kasih',
                  'makasih', 'good', 'great', 'nice', 'love', 'sip', 'oke', 'mantul',
                  'top', 'joss', 'luar biasa', 'amazing', 'setuju']
negative_words = ['susah', 'sulit', 'gagal', 'sedih', 'marah', 'kesel', 'bosan',
                  'males', 'capek', 'ribet', 'masalah', 'error', 'bug', 'stuck', 'bad']

pos_emojis = ['👍', '🔥', '✅', '🙌', '🎉', '💪', '❤️', '😁', '🥳', '👏']
neg_emojis = ['😭', '😬', '😡', '💔', '😢', '😞']

msgs_text = user_msgs['message'].str.lower()

pos_count = sum(msgs_text.str.contains(w, na=False).sum() for w in positive_words)
neg_count = sum(msgs_text.str.contains(w, na=False).sum() for w in negative_words)

pos_emoji_count = sum(emoji_counter.get(e, 0) for e in pos_emojis)
neg_emoji_count = sum(emoji_counter.get(e, 0) for e in neg_emojis)

total_pos = pos_count + pos_emoji_count
total_neg = neg_count + neg_emoji_count

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("😊 Positive Signals", f"{total_pos:,}")
with col2:
    st.metric("😟 Negative Signals", f"{total_neg:,}")
with col3:
    ratio = total_pos / max(total_neg, 1)
    mood = "🟢 Very Positive" if ratio > 3 else "🟡 Positive" if ratio > 1.5 else "🔴 Mixed"
    st.metric("📊 Positivity Ratio", f"{ratio:.1f}x", delta=mood)

# Breakdown table
st.markdown("##### Positive Keywords")
pos_data = {w: msgs_text.str.contains(w, na=False).sum() for w in positive_words}
pos_data = dict(sorted(pos_data.items(), key=lambda x: x[1], reverse=True))
pos_df = pd.DataFrame(list(pos_data.items()), columns=['Keyword', 'Count'])
pos_df = pos_df[pos_df['Count'] > 0]
st.dataframe(pos_df, use_container_width=True, hide_index=True, height=200)

st.divider()

# ── HUMOR INDEX (wkwk) ──────────────────────────────────────────────────────
st.markdown("### 😆 Humor Index (Indonesian Laughter)")

laugh_patterns = {
    'wkwk+': len(msgs_text[msgs_text.str.contains('wkwk', na=False)]),
    'haha+': len(msgs_text[msgs_text.str.contains('haha', na=False)]),
    'wkwkwk+': len(msgs_text[msgs_text.str.contains('wkwkwk', na=False)]),
    'hehe': len(msgs_text[msgs_text.str.contains('hehe', na=False)]),
    '🤣': emoji_counter.get('🤣', 0),
    '😂': emoji_counter.get('😂', 0),
    '😆': emoji_counter.get('😆', 0),
}
laugh_df = pd.DataFrame(list(laugh_patterns.items()), columns=['Pattern', 'Count'])
laugh_df = laugh_df.sort_values('Count', ascending=False)

fig = px.bar(laugh_df, x='Pattern', y='Count',
             color_discrete_sequence=['#f59e0b'], text='Count')
fig.update_traces(textposition='outside', textfont_size=11)
apply_chart_theme(fig)
fig.update_layout(height=300)
st.plotly_chart(fig, use_container_width=True)

# ── EXPORT ───────────────────────────────────────────────────────────────────
st.divider()
with st.expander("📥 Export Emoji Data"):
    if top_emojis:
        export_buttons(emoji_df, "emoji_export", "emoji_analysis")
