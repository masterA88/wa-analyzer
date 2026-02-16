"""
💬 Topics & Content Analysis
=============================
Word cloud, topic tracking, shared resources, and keyword search.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from collections import Counter
from utils.parser import analyze_topics, get_topic_trend, extract_urls, TOPIC_KEYWORDS
from utils.helpers import (apply_chart_theme, CHART_COLORS, ALL_STOPWORDS,
                           date_range_filter, export_buttons)

st.set_page_config(page_title="Topics", page_icon="💬", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("⬅️ Please upload a chat file on the main page first.")
    st.stop()

df = st.session_state.df.copy()

st.markdown("## 💬 Topics & Content Analysis")

with st.expander("🗓️ Filter by Date Range", expanded=False):
    df, _, _ = date_range_filter(df, "topics")

user_msgs = df[~df['is_system'] & (df['msg_type'] == 'text')]

# ── WORD CLOUD ───────────────────────────────────────────────────────────────
st.markdown("### ☁️ Word Cloud")

@st.cache_data
def generate_word_freq(_msgs):
    all_text = ' '.join(_msgs['message'].str.lower().tolist())
    words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text)
    filtered = [w for w in words if w not in ALL_STOPWORDS]
    return Counter(filtered)

word_freq = generate_word_freq(user_msgs)

try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt

    wc = WordCloud(
        width=1000, height=400,
        background_color='#0f172a',
        colormap='winter',
        max_words=100,
        min_font_size=10,
        max_font_size=80,
        prefer_horizontal=0.7,
    ).generate_from_frequencies(word_freq)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    fig.patch.set_facecolor('#0f172a')
    st.pyplot(fig)
    plt.close()
except ImportError:
    st.info("Install `wordcloud` for the word cloud visualization: `pip install wordcloud`")
    # Fallback: show top words as bar chart
    top_words = pd.DataFrame(word_freq.most_common(30), columns=['word', 'count'])
    fig = px.bar(top_words, x='count', y='word', orientation='h',
                 color_discrete_sequence=['#10b981'])
    apply_chart_theme(fig)
    fig.update_layout(height=600, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── TOPIC FREQUENCY ──────────────────────────────────────────────────────────
st.markdown("### 📊 Topic Frequency")

topic_counts = analyze_topics(df)
topic_df = pd.DataFrame(list(topic_counts.items()), columns=['Topic', 'Mentions'])
topic_df = topic_df[topic_df['Mentions'] > 0].sort_values('Mentions', ascending=True)

fig = px.bar(topic_df, x='Mentions', y='Topic', orientation='h',
             color='Mentions', color_continuous_scale=['#1e293b', '#0ea5e9'],
             text='Mentions')
fig.update_traces(texttemplate='%{text:,}', textposition='outside', textfont_size=11)
apply_chart_theme(fig)
fig.update_layout(height=max(350, len(topic_df) * 35),
                  coloraxis_showscale=False,
                  yaxis_title="", xaxis_title="Mentions")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── TOPIC TREND OVER TIME ───────────────────────────────────────────────────
st.markdown("### 📈 Topic Trend Over Time")

selected_topic = st.selectbox("Select topic:", list(TOPIC_KEYWORDS.keys()),
                                key="topic_trend_select")

trend = get_topic_trend(df, selected_topic)
if not trend.empty:
    trend['date'] = pd.to_datetime(trend['date'])
    fig = px.line(trend, x='date', y='count',
                  color_discrete_sequence=['#10b981'])
    fig.update_traces(line_width=2)
    apply_chart_theme(fig)
    fig.update_layout(height=300, xaxis_title="", yaxis_title="Mentions")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data for this topic in selected range.")

st.divider()

# ── SHARED LINKS / RESOURCES ────────────────────────────────────────────────
st.markdown("### 🔗 Shared Resources & Links")

@st.cache_data
def get_url_data(_df):
    return extract_urls(_df)

url_df = get_url_data(df)

if not url_df.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Top Domains")
        domain_counts = url_df['domain'].value_counts().head(15).reset_index()
        domain_counts.columns = ['Domain', 'Count']

        fig = px.bar(domain_counts, x='Count', y='Domain', orientation='h',
                     color_discrete_sequence=['#8b5cf6'], text='Count')
        fig.update_traces(textposition='outside', textfont_size=11)
        apply_chart_theme(fig)
        fig.update_layout(height=400, yaxis=dict(autorange="reversed", title=""))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Recent Links")
        recent = url_df.sort_values('date', ascending=False).head(20)
        st.dataframe(
            recent[['date', 'user', 'domain', 'url']],
            use_container_width=True,
            hide_index=True,
            column_config={
                'url': st.column_config.LinkColumn("URL", display_text="🔗 Open"),
                'date': st.column_config.DateColumn("Date", format="DD/MM/YY"),
            },
            height=400,
        )
else:
    st.info("No URLs found in messages.")

st.divider()

# ── LONG-FORM CONTENT (TUTORIALS) ───────────────────────────────────────────
st.markdown("### 📚 Long-Form Messages (Potential Tutorials/Guides)")

long_msgs = user_msgs[user_msgs['char_count'] > 300].sort_values('char_count', ascending=False)

if not long_msgs.empty:
    st.markdown(f"Found **{len(long_msgs)}** messages with 300+ characters")

    for i, (_, row) in enumerate(long_msgs.head(10).iterrows()):
        with st.expander(f"📝 {row['user']} — {row['date']} ({row['char_count']} chars)"):
            st.text(row['message'][:1000] + ("..." if len(row['message']) > 1000 else ""))

# ── KEYWORD SEARCH ───────────────────────────────────────────────────────────
st.divider()
st.markdown("### 🔍 Keyword Search")

query = st.text_input("Search messages:", placeholder="Type a keyword...",
                        key="topic_search")

if query:
    from utils.parser import search_messages
    results = search_messages(df, query)
    results_user = results[~results['is_system']]

    st.markdown(f"Found **{len(results_user)}** messages containing '{query}'")

    if not results_user.empty:
        st.dataframe(
            results_user[['date', 'user', 'message']].head(50),
            use_container_width=True,
            hide_index=True,
            height=400,
        )
        with st.expander("📥 Export Search Results"):
            export_buttons(results_user[['date', 'user', 'message']], "search", f"search_{query}")

# ── EXPORT ───────────────────────────────────────────────────────────────────
st.divider()
with st.expander("📥 Export Topics Data"):
    export_buttons(topic_df, "topics_export", "topic_analysis")
    if not url_df.empty:
        st.markdown("---")
        st.markdown("##### Links Export")
        export_buttons(url_df, "urls_export", "shared_links")
