"""
🏆 User Leaderboard
====================
Ranked user activity, engagement scores, and per-user breakdowns.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import apply_chart_theme, CHART_COLORS, date_range_filter, export_buttons
from utils.parser import extract_emojis_from_text

st.set_page_config(page_title="Leaderboard", page_icon="🏆", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("⬅️ Please upload a chat file on the main page first.")
    st.stop()

df = st.session_state.df.copy()

st.markdown("## 🏆 User Leaderboard")

# ── FILTERS ──────────────────────────────────────────────────────────────────
with st.expander("🗓️ Filter by Date Range", expanded=False):
    df, _, _ = date_range_filter(df, "leader")

user_msgs = df[~df['is_system'] & (df['user'] != 'system')]

# ── TOP N SELECTOR ───────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 3])
with col1:
    top_n = st.selectbox("Show Top", [5, 10, 20, 50, "All Users"],
                          index=1, key="leaderboard_top_n")

# ── BUILD USER STATS ─────────────────────────────────────────────────────────
@st.cache_data
def compute_user_stats(_user_msgs):
    stats = _user_msgs.groupby('user').agg(
        total_messages=('message', 'size'),
        avg_msg_length=('char_count', 'mean'),
        total_words=('word_count', 'sum'),
        media_sent=('is_media', 'sum'),
        first_seen=('date', 'min'),
        last_seen=('date', 'max'),
        active_days=('date', 'nunique'),
    ).reset_index()

    stats['avg_msg_length'] = stats['avg_msg_length'].round(1)
    stats = stats.sort_values('total_messages', ascending=False).reset_index(drop=True)
    stats['rank'] = stats.index + 1
    return stats

stats = compute_user_stats(user_msgs)

if top_n != "All Users":
    display_stats = stats.head(int(top_n))
else:
    display_stats = stats

# ── BAR CHART ────────────────────────────────────────────────────────────────
st.markdown(f"### Top {top_n if top_n != 'All Users' else stats.shape[0]} Active Users")

chart_data = display_stats.head(30)  # Max 30 bars for readability

fig = px.bar(
    chart_data,
    x='total_messages', y='user',
    orientation='h',
    color='total_messages',
    color_continuous_scale=['#1e3a5f', '#10b981'],
    text='total_messages',
)
fig.update_traces(texttemplate='%{text:,}', textposition='outside',
                  textfont_size=11)
apply_chart_theme(fig)
fig.update_layout(
    height=max(400, len(chart_data) * 28),
    yaxis=dict(autorange="reversed", title=""),
    xaxis_title="Messages",
    coloraxis_showscale=False,
    margin=dict(l=150),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── DETAILED TABLE ───────────────────────────────────────────────────────────
st.markdown("### 📋 Detailed User Statistics")

table_df = display_stats[['rank', 'user', 'total_messages', 'avg_msg_length',
                           'total_words', 'media_sent', 'active_days',
                           'first_seen', 'last_seen']].copy()

table_df.columns = ['#', 'User', 'Messages', 'Avg Length', 'Words',
                     'Media', 'Active Days', 'First Seen', 'Last Seen']

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        '#': st.column_config.NumberColumn(width="small"),
        'Messages': st.column_config.NumberColumn(format="%d"),
        'Avg Length': st.column_config.NumberColumn(format="%.1f"),
    },
    height=min(600, len(table_df) * 38 + 40),
)

st.divider()

# ── ACTIVITY HEATMAP (User × Hour) ──────────────────────────────────────────
st.markdown("### 🕐 Activity Heatmap — User × Hour of Day")
st.caption("Top 15 users shown")

top15 = stats.head(15)['user'].tolist()
heatmap_data = user_msgs[user_msgs['user'].isin(top15)].copy()
pivot = heatmap_data.pivot_table(index='user', columns='hour', values='message',
                                  aggfunc='count', fill_value=0)
# Reorder by total activity
pivot = pivot.loc[top15]

fig = px.imshow(
    pivot,
    labels=dict(x="Hour", y="User", color="Messages"),
    color_continuous_scale=["#0f172a", "#10b981"],
    aspect="auto",
)
apply_chart_theme(fig)
fig.update_layout(height=450, xaxis=dict(dtick=1))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── USER TYPES PIE ───────────────────────────────────────────────────────────
st.markdown("### 👥 User Engagement Tiers")

def categorize_user(msg_count):
    if msg_count >= 100:
        return "🔥 Power User (100+)"
    elif msg_count >= 20:
        return "⭐ Active (20-99)"
    elif msg_count >= 5:
        return "💬 Casual (5-19)"
    else:
        return "👻 Lurker (<5)"

stats['tier'] = stats['total_messages'].apply(categorize_user)
tier_counts = stats['tier'].value_counts().reset_index()
tier_counts.columns = ['tier', 'count']

col1, col2 = st.columns([1, 1])

with col1:
    fig = px.pie(tier_counts, values='count', names='tier',
                 color_discrete_sequence=['#ef4444', '#f59e0b', '#10b981', '#64748b'],
                 hole=0.5)
    fig.update_traces(textinfo='label+value', textfont_size=11)
    apply_chart_theme(fig)
    fig.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("")
    st.markdown("")
    for _, row in tier_counts.iterrows():
        pct = row['count'] / len(stats) * 100
        st.markdown(f"**{row['tier']}** — {row['count']} users ({pct:.1f}%)")

# ── EXPORT ───────────────────────────────────────────────────────────────────
st.divider()
with st.expander("📥 Export User Statistics"):
    export_buttons(stats, "leaderboard", "user_leaderboard")
