"""
⏰ Temporal Analytics
=====================
Time-based patterns: hourly, daily, weekly rhythms and calendar heatmap.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import apply_chart_theme, CHART_COLORS, date_range_filter, export_buttons

st.set_page_config(page_title="Temporal", page_icon="⏰", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("⬅️ Please upload a chat file on the main page first.")
    st.stop()

df = st.session_state.df.copy()

st.markdown("## ⏰ Temporal Analytics")

with st.expander("🗓️ Filter by Date Range", expanded=False):
    df, _, _ = date_range_filter(df, "temporal")

user_msgs = df[~df['is_system'] & (df['user'] != 'system')]

# ── HOURLY DISTRIBUTION ─────────────────────────────────────────────────────
st.markdown("### 🕐 Hourly Activity Distribution")

hourly = user_msgs.groupby('hour').size().reset_index(name='messages')
# Fill missing hours
all_hours = pd.DataFrame({'hour': range(24)})
hourly = all_hours.merge(hourly, on='hour', how='left').fillna(0)
hourly['messages'] = hourly['messages'].astype(int)

peak_hour = hourly.loc[hourly['messages'].idxmax(), 'hour']
quiet_hour = hourly.loc[hourly['messages'].idxmin(), 'hour']

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🔥 Peak Hour", f"{int(peak_hour):02d}:00")
with col2:
    st.metric("😴 Quietest Hour", f"{int(quiet_hour):02d}:00")
with col3:
    st.metric("📊 Peak Messages", f"{hourly['messages'].max():,}")

fig = px.bar(hourly, x='hour', y='messages',
             color='messages',
             color_continuous_scale=['#1e293b', '#10b981'],
             text='messages')
fig.update_traces(texttemplate='%{text:,}', textposition='outside', textfont_size=10)
apply_chart_theme(fig)
fig.update_layout(
    height=350,
    xaxis=dict(dtick=1, title="Hour of Day"),
    yaxis_title="Messages",
    coloraxis_showscale=False,
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── DAY OF WEEK ──────────────────────────────────────────────────────────────
st.markdown("### 📆 Day of Week Distribution")

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
daily_dow = user_msgs.groupby('day_of_week').size().reset_index(name='messages')
daily_dow['day_of_week'] = pd.Categorical(daily_dow['day_of_week'], categories=day_order, ordered=True)
daily_dow = daily_dow.sort_values('day_of_week')

fig = px.bar(daily_dow, x='day_of_week', y='messages',
             color='messages',
             color_continuous_scale=['#1e293b', '#0ea5e9'],
             text='messages')
fig.update_traces(texttemplate='%{text:,}', textposition='outside', textfont_size=11)
apply_chart_theme(fig)
fig.update_layout(height=350, xaxis_title="", yaxis_title="Messages",
                  coloraxis_showscale=False)
st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    weekday = daily_dow[daily_dow['day_of_week'].isin(day_order[:5])]['messages'].sum()
    st.metric("Mon-Fri (Weekday)", f"{weekday:,}")
with col2:
    weekend = daily_dow[daily_dow['day_of_week'].isin(day_order[5:])]['messages'].sum()
    st.metric("Sat-Sun (Weekend)", f"{weekend:,}")

st.divider()

# ── CALENDAR HEATMAP ─────────────────────────────────────────────────────────
st.markdown("### 📅 Calendar Heatmap (GitHub-style)")

daily_counts = user_msgs.groupby('date').size().reset_index(name='messages')
daily_counts['date'] = pd.to_datetime(daily_counts['date'])
daily_counts['week'] = daily_counts['date'].dt.isocalendar().week.astype(int)
daily_counts['weekday'] = daily_counts['date'].dt.weekday  # 0=Mon, 6=Sun
daily_counts['month_year'] = daily_counts['date'].dt.strftime('%Y-%m')

# Create a proper calendar heatmap using Plotly
daily_counts['day_name'] = daily_counts['date'].dt.strftime('%A')
daily_counts['week_start'] = daily_counts['date'] - pd.to_timedelta(daily_counts['weekday'], unit='D')

fig = go.Figure(go.Heatmap(
    x=daily_counts['week_start'],
    y=daily_counts['day_name'],
    z=daily_counts['messages'],
    colorscale=[[0, '#0f172a'], [0.3, '#064e3b'], [0.6, '#10b981'], [1.0, '#34d399']],
    hovertemplate='%{x|%b %d}<br>%{y}<br>%{z} messages<extra></extra>',
    showscale=True,
    colorbar=dict(title="Msgs", thickness=15),
))

apply_chart_theme(fig)
fig.update_layout(
    height=280,
    yaxis=dict(
        categoryorder='array',
        categoryarray=['Sunday', 'Saturday', 'Friday', 'Thursday', 'Wednesday', 'Tuesday', 'Monday'],
    ),
    xaxis=dict(title=""),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── BUSIEST DAYS ─────────────────────────────────────────────────────────────
st.markdown("### 🔥 Top 10 Busiest Days")

top_days = daily_counts.nlargest(10, 'messages')[['date', 'messages', 'day_name']].copy()
top_days['date_str'] = top_days['date'].dt.strftime('%d %b %Y')

fig = px.bar(top_days, x='messages', y='date_str', orientation='h',
             color_discrete_sequence=['#f59e0b'],
             text='messages')
fig.update_traces(texttemplate='%{text:,}', textposition='outside', textfont_size=11)
apply_chart_theme(fig)
fig.update_layout(
    height=380,
    yaxis=dict(autorange="reversed", title=""),
    xaxis_title="Messages",
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── HOUR × DAY HEATMAP ──────────────────────────────────────────────────────
st.markdown("### 🗓️ Hour × Day Heatmap")

pivot = user_msgs.pivot_table(
    index='day_of_week', columns='hour',
    values='message', aggfunc='count', fill_value=0
)
# Reorder days
pivot = pivot.reindex(day_order)

fig = px.imshow(
    pivot,
    labels=dict(x="Hour", y="Day", color="Messages"),
    color_continuous_scale=["#0f172a", "#10b981"],
    aspect="auto",
)
apply_chart_theme(fig)
fig.update_layout(height=300, xaxis=dict(dtick=1))
st.plotly_chart(fig, use_container_width=True)

# ── EXPORT ───────────────────────────────────────────────────────────────────
st.divider()
with st.expander("📥 Export Temporal Data"):
    export_buttons(daily_counts[['date', 'messages', 'day_name']], "temporal", "temporal_data")
