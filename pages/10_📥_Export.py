"""
📥 Export Center
=================
Universal export hub — download any data as CSV, Excel, or filtered subsets.
"""

import streamlit as st
import pandas as pd
import io
from utils.parser import extract_member_directory, extract_urls
from utils.helpers import df_to_csv, df_to_excel, date_range_filter

st.set_page_config(page_title="Export", page_icon="📥", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("⬅️ Please upload a chat file on the main page first.")
    st.stop()

df = st.session_state.df.copy()

st.markdown("## 📥 Export Center")
st.caption("Download any data from your chat analysis")

# ── DATE FILTER (optional) ───────────────────────────────────────────────────
with st.expander("🗓️ Filter by Date Range (applies to all exports)", expanded=False):
    df, start_date, end_date = date_range_filter(df, "export")

st.divider()

# ── EXPORT SECTIONS ──────────────────────────────────────────────────────────

# 1. Full Chat Data
st.markdown("### 💬 Full Chat Data")
st.markdown(f"All parsed messages: **{len(df):,}** rows")

col1, col2, col3 = st.columns(3)

export_df = df[['date', 'time', 'hour', 'day_of_week', 'user', 'message',
                 'msg_type', 'is_media', 'is_system', 'word_count', 'char_count']].copy()
export_df['date'] = export_df['date'].astype(str)
export_df['time'] = export_df['time'].astype(str)

with col1:
    st.download_button(
        "📥 Download CSV",
        data=df_to_csv(export_df),
        file_name="chat_data_full.csv",
        mime="text/csv",
        use_container_width=True,
    )
with col2:
    st.download_button(
        "📥 Download Excel",
        data=df_to_excel(export_df),
        file_name="chat_data_full.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
with col3:
    json_data = export_df.to_json(orient='records', indent=2, force_ascii=False)
    st.download_button(
        "📥 Download JSON",
        data=json_data,
        file_name="chat_data_full.json",
        mime="application/json",
        use_container_width=True,
    )

st.divider()

# 2. User Statistics
st.markdown("### 👥 User Statistics")

user_msgs = df[~df['is_system'] & (df['user'] != 'system')]
user_stats = user_msgs.groupby('user').agg(
    total_messages=('message', 'size'),
    avg_msg_length=('char_count', 'mean'),
    total_words=('word_count', 'sum'),
    media_sent=('is_media', 'sum'),
    first_seen=('date', 'min'),
    last_seen=('date', 'max'),
    active_days=('date', 'nunique'),
).reset_index().sort_values('total_messages', ascending=False)

user_stats['avg_msg_length'] = user_stats['avg_msg_length'].round(1)
user_stats['first_seen'] = user_stats['first_seen'].astype(str)
user_stats['last_seen'] = user_stats['last_seen'].astype(str)

st.markdown(f"**{len(user_stats)}** users")
col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "📥 User Stats CSV",
        data=df_to_csv(user_stats),
        file_name="user_statistics.csv",
        mime="text/csv",
        use_container_width=True,
    )
with col2:
    st.download_button(
        "📥 User Stats Excel",
        data=df_to_excel(user_stats),
        file_name="user_statistics.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

st.divider()

# 3. Member Directory
st.markdown("### 📇 Member Directory")

members = extract_member_directory(df)
if not members.empty:
    members_export = members.copy()
    members_export['date'] = members_export['date'].astype(str)
    st.markdown(f"**{len(members)}** verified members with profiles")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Directory CSV",
            data=df_to_csv(members_export),
            file_name="member_directory.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "📥 Directory Excel",
            data=df_to_excel(members_export),
            file_name="member_directory.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
else:
    st.info("No structured member introductions found.")

st.divider()

# 4. Shared Links
st.markdown("### 🔗 Shared Links & Resources")

urls_df = extract_urls(df)
if not urls_df.empty:
    urls_export = urls_df.copy()
    urls_export['date'] = urls_export['date'].astype(str)
    st.markdown(f"**{len(urls_df)}** URLs shared across **{urls_df['domain'].nunique()}** domains")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Links CSV",
            data=df_to_csv(urls_export),
            file_name="shared_links.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "📥 Links Excel",
            data=df_to_excel(urls_export),
            file_name="shared_links.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
else:
    st.info("No URLs found.")

st.divider()

# 5. Filtered Export (by user)
st.markdown("### 🎯 Custom Filtered Export")

col1, col2 = st.columns(2)
with col1:
    selected_users = st.multiselect(
        "Select specific users:",
        sorted(user_msgs['user'].unique()),
        key="export_users"
    )
with col2:
    export_format = st.selectbox("Format:", ["CSV", "Excel", "JSON"],
                                   key="export_format")

if selected_users:
    filtered_export = user_msgs[user_msgs['user'].isin(selected_users)].copy()
    filtered_export = filtered_export[['date', 'time', 'user', 'message', 'msg_type',
                                        'word_count', 'char_count']].copy()
    filtered_export['date'] = filtered_export['date'].astype(str)
    filtered_export['time'] = filtered_export['time'].astype(str)

    st.markdown(f"**{len(filtered_export):,}** messages from selected users")

    if export_format == "CSV":
        data = df_to_csv(filtered_export)
        mime = "text/csv"
        ext = "csv"
    elif export_format == "Excel":
        data = df_to_excel(filtered_export)
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"
    else:
        data = filtered_export.to_json(orient='records', indent=2, force_ascii=False)
        mime = "application/json"
        ext = "json"

    st.download_button(
        f"📥 Download Filtered Data ({export_format})",
        data=data,
        file_name=f"filtered_chat.{ext}",
        mime=mime,
        use_container_width=True,
    )

st.divider()

# 6. Daily Summary Export
st.markdown("### 📅 Daily Summary")

daily = user_msgs.groupby('date').agg(
    messages=('message', 'size'),
    users=('user', 'nunique'),
    media=('is_media', 'sum'),
    avg_length=('char_count', 'mean'),
).reset_index()
daily['avg_length'] = daily['avg_length'].round(1)
daily['date'] = daily['date'].astype(str)

col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "📥 Daily Summary CSV",
        data=df_to_csv(daily),
        file_name="daily_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )
with col2:
    st.download_button(
        "📥 Daily Summary Excel",
        data=df_to_excel(daily),
        file_name="daily_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
