"""
📊 Overview Dashboard
=====================
Group-level KPIs, activity trends, and high-level health metrics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import apply_chart_theme, CHART_COLORS, metric_card, date_range_filter, export_buttons

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

# ── GUARD ────────────────────────────────────────────────────────────────────
if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("⬅️ Please upload a chat file on the main page first.")
    st.stop()

df = st.session_state.df.copy()

st.markdown("## 📊 Overview Dashboard")

# ── DATE FILTER ──────────────────────────────────────────────────────────────
with st.expander("🗓️ Filter by Date Range", expanded=False):
    df, start_date, end_date = date_range_filter(df, "overview")

user_msgs = df[~df['is_system']]
total_days = (df['date'].max() - df['date'].min()).days + 1

# ── KPI ROW ──────────────────────────────────────────────────────────────────
st.markdown("### Key Metrics")
cols = st.columns(6)

kpis = [
    ("💬", "Total Messages", f"{len(user_msgs):,}"),
    ("👥", "Unique Users", f"{user_msgs['user'].nunique()}"),
    ("📅", "Days Active", f"{total_days}"),
    ("📊", "Avg Msgs/Day", f"{len(user_msgs)/max(total_days,1):.0f}"),
    ("📝", "Avg Msg Length", f"{user_msgs['char_count'].mean():.0f} chars"),
    ("🖼️", "Media Shared", f"{df['is_media'].sum():,}"),
]

for col, (icon, label, val) in zip(cols, kpis):
    with col:
        metric_card(label, val, icon)

st.divider()

# ── MESSAGE VOLUME TREND ─────────────────────────────────────────────────────
st.markdown("### 📈 Message Volume Over Time")

agg_option = st.radio("Aggregate by:", ["Daily", "Weekly", "Monthly"],
                       horizontal=True, key="overview_agg")

daily = user_msgs.groupby('date').size().reset_index(name='messages')
daily['date'] = pd.to_datetime(daily['date'])

if agg_option == "Weekly":
    daily = daily.set_index('date').resample('W')['messages'].sum().reset_index()
elif agg_option == "Monthly":
    daily = daily.set_index('date').resample('ME')['messages'].sum().reset_index()

fig = px.area(daily, x='date', y='messages',
              color_discrete_sequence=['#10b981'])
fig.update_traces(line_width=2, fill='tozeroy',
                  fillcolor='rgba(16, 185, 129, 0.1)')
apply_chart_theme(fig)
fig.update_layout(height=350, xaxis_title="", yaxis_title="Messages")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── MESSAGE TYPE BREAKDOWN ───────────────────────────────────────────────────
st.markdown("### 📋 Message Breakdown")

col1, col2 = st.columns(2)

with col1:
    # Message types
    type_counts = df['msg_type'].value_counts().reset_index()
    type_counts.columns = ['type', 'count']
    type_counts = type_counts[type_counts['type'] != 'system']

    fig = px.pie(type_counts, values='count', names='type',
                 color_discrete_sequence=CHART_COLORS,
                 hole=0.55)
    fig.update_traces(textinfo='label+percent', textfont_size=11)
    apply_chart_theme(fig)
    fig.update_layout(height=350, title="Message Types",
                      showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Media breakdown
    media_types = {
        'Images': df['message'].str.contains('image omitted', na=False).sum(),
        'Stickers': df['message'].str.contains('sticker omitted', na=False).sum(),
        'Videos': df['message'].str.contains('video omitted', na=False).sum(),
        'Documents': df['message'].str.contains('document omitted', na=False).sum(),
        'GIFs': df['message'].str.contains('GIF omitted', na=False).sum(),
        'Audio': df['message'].str.contains('audio omitted', na=False).sum(),
    }
    media_df = pd.DataFrame(list(media_types.items()), columns=['type', 'count'])
    media_df = media_df[media_df['count'] > 0].sort_values('count', ascending=True)

    fig = px.bar(media_df, x='count', y='type', orientation='h',
                 color_discrete_sequence=['#0ea5e9'])
    apply_chart_theme(fig)
    fig.update_layout(height=350, title="Media Types",
                      xaxis_title="Count", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── SYSTEM EVENTS ────────────────────────────────────────────────────────────
st.markdown("### 🔔 System Events")
cols = st.columns(4)

events = {
    '🟢 Joins': df[df['msg_type'] == 'join'].shape[0],
    '🔴 Leaves': df[df['msg_type'] == 'leave'].shape[0],
    '✏️ Edits': (df['message'].str.contains('edited', na=False)).sum(),
    '🗑️ Deletions': (df['message'].str.contains('deleted', na=False)).sum(),
}

for col, (label, count) in zip(cols, events.items()):
    with col:
        st.metric(label, f"{count:,}")

# ── GROUP GROWTH ─────────────────────────────────────────────────────────────
st.divider()
st.markdown("### 📈 Group Growth (Cumulative Unique Users)")

first_msg = user_msgs.groupby('user')['date'].min().reset_index()
first_msg.columns = ['user', 'first_date']
first_msg['first_date'] = pd.to_datetime(first_msg['first_date'])
growth = first_msg.groupby('first_date').size().cumsum().reset_index(name='total_users')

fig = px.line(growth, x='first_date', y='total_users',
              color_discrete_sequence=['#8b5cf6'])
fig.update_traces(line_width=2.5)
apply_chart_theme(fig)
fig.update_layout(height=300, xaxis_title="", yaxis_title="Cumulative Users")
st.plotly_chart(fig, use_container_width=True)

# ── EXPORT ───────────────────────────────────────────────────────────────────
st.divider()
with st.expander("📥 Export Overview Data"):
    summary = pd.DataFrame({
        'Date': daily['date'],
        'Messages': daily['messages'],
    })
    export_buttons(summary, "overview", "overview_data")
