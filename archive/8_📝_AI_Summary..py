"""
📝 AI Chat Summary
===================
LLM-powered summarization with date range selection.
Designed for plug-and-play with any free LLM API.

Supported backends (all have free tiers):
- Google Gemini (free: 15 RPM)
- Anthropic Claude (free trial credits)
- OpenAI GPT (free trial credits)
- Groq (free: generous limits)
- Local Ollama (completely free)
"""

import streamlit as st
import pandas as pd
from utils.helpers import date_range_filter, export_buttons

st.set_page_config(page_title="AI Summary", page_icon="📝", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("⬅️ Please upload a chat file on the main page first.")
    st.stop()

df = st.session_state.df.copy()

st.markdown("## 📝 AI Chat Summary")
st.caption("Summarize group conversations with AI — select a time range and get key insights")

# ── DATE RANGE SELECTOR ─────────────────────────────────────────────────────
st.markdown("### 🗓️ Select Time Range to Summarize")
filtered, start_date, end_date = date_range_filter(df, "summary")

user_msgs = filtered[~filtered['is_system'] & (filtered['user'] != 'system')]

st.info(f"📊 **{len(user_msgs):,}** messages from **{user_msgs['user'].nunique()}** users "
        f"between {start_date} and {end_date}")

# ── FILTER OPTIONS ───────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    summary_mode = st.selectbox("Summary Mode:", [
        "Quick Summary (1 paragraph)",
        "Detailed Summary (bullet points)",
        "Key Decisions & Announcements",
        "Topic-Filtered Summary",
    ], key="summary_mode")

with col2:
    if summary_mode == "Topic-Filtered Summary":
        topic_filter = st.text_input("Filter by topic keyword:",
                                      placeholder="e.g., SQL, job, interview",
                                      key="summary_topic")
    else:
        topic_filter = None

# ── LLM CONFIGURATION ───────────────────────────────────────────────────────
st.divider()
st.markdown("### ⚙️ AI Provider Configuration")

with st.expander("Configure AI Provider", expanded=False):
    provider = st.selectbox("Provider:", [
        "🔌 Not Configured (Manual Summary Below)",
        "🟢 Google Gemini (Free Tier)",
        "🟣 Groq (Free Tier)",
        "🔵 OpenAI",
        "🟠 Anthropic Claude",
        "🏠 Local Ollama",
    ], key="ai_provider")

    if provider != "🔌 Not Configured (Manual Summary Below)":
        api_key = st.text_input("API Key:", type="password", key="ai_key",
                                 help="Your API key is NOT stored — session only")

        st.markdown("""
        **Free tier options:**
        - **Google Gemini**: [Get free API key](https://aistudio.google.com/) — 15 requests/min
        - **Groq**: [Get free API key](https://console.groq.com/) — very fast, generous limits
        - **Ollama**: [Install locally](https://ollama.ai/) — 100% free, runs on your machine
        """)


# ── PREPARE CONTEXT ──────────────────────────────────────────────────────────
def prepare_summary_context(msgs_df, max_chars=12000):
    """Prepare chat messages for LLM summarization."""
    if topic_filter:
        msgs_df = msgs_df[msgs_df['message'].str.contains(topic_filter, case=False, na=False)]

    # Format messages
    lines = []
    for _, row in msgs_df.iterrows():
        lines.append(f"[{row['date']}] {row['user']}: {row['message'][:200]}")

    text = '\n'.join(lines)
    if len(text) > max_chars:
        # Smart truncation: keep beginning and end
        half = max_chars // 2
        text = text[:half] + f"\n\n... [{len(lines)} total messages, truncated for context] ...\n\n" + text[-half:]

    return text


context = prepare_summary_context(user_msgs)

# ── GENERATE SUMMARY ─────────────────────────────────────────────────────────
st.divider()

if st.button("🚀 Generate Summary", type="primary", use_container_width=True):
    if provider == "🔌 Not Configured (Manual Summary Below)":
        # Rule-based summary (no AI needed)
        st.markdown("### 📋 Auto-Generated Summary (Rule-Based)")

        total = len(user_msgs)
        top_users = user_msgs['user'].value_counts().head(5)
        active_days = user_msgs['date'].nunique()

        # Find most discussed topics
        from utils.parser import analyze_topics
        topics = analyze_topics(filtered)
        top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]

        st.markdown(f"""
        **Period:** {start_date} to {end_date} ({active_days} active days)

        **Activity:** {total:,} messages from {user_msgs['user'].nunique()} users
        (avg {total // max(active_days, 1)} msgs/day)

        **Most Active Users:**
        """)
        for user, count in top_users.items():
            st.markdown(f"- **{user}**: {count:,} messages ({count/total*100:.1f}%)")

        st.markdown("**Hot Topics:**")
        for topic, count in top_topics:
            if count > 0:
                st.markdown(f"- **{topic}**: {count} mentions")

        # Shared links summary
        from utils.parser import extract_urls
        urls = extract_urls(filtered)
        if not urls.empty:
            st.markdown(f"**Links Shared:** {len(urls)} URLs from {urls['domain'].nunique()} domains")
            top_domains = urls['domain'].value_counts().head(3)
            for domain, count in top_domains.items():
                st.markdown(f"- {domain}: {count} links")

    elif provider == "🟢 Google Gemini (Free Tier)":
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            prompt = f"""Analyze this WhatsApp group chat and provide a {summary_mode.lower()}.
Focus on: key discussions, decisions made, important announcements, action items.

Chat messages:
{context}"""

            with st.spinner("🤖 Gemini is thinking..."):
                response = model.generate_content(prompt)
                st.markdown("### 🤖 AI Summary")
                st.markdown(response.text)
        except ImportError:
            st.error("Install: `pip install google-generativeai`")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    elif provider == "🟣 Groq (Free Tier)":
        try:
            from groq import Groq
            client = Groq(api_key=api_key)

            prompt = f"""Analyze this WhatsApp group chat and provide a {summary_mode.lower()}.
Focus on: key discussions, decisions made, important announcements, action items.

Chat messages:
{context}"""

            with st.spinner("🤖 Groq is thinking..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                )
                st.markdown("### 🤖 AI Summary")
                st.markdown(response.choices[0].message.content)
        except ImportError:
            st.error("Install: `pip install groq`")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    elif provider == "🔵 OpenAI":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            prompt = f"""Analyze this WhatsApp group chat and provide a {summary_mode.lower()}.
Focus on: key discussions, decisions made, important announcements, action items.

Chat messages:
{context}"""

            with st.spinner("🤖 GPT is thinking..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                )
                st.markdown("### 🤖 AI Summary")
                st.markdown(response.choices[0].message.content)
        except ImportError:
            st.error("Install: `pip install openai`")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    elif provider == "🟠 Anthropic Claude":
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)

            prompt = f"""Analyze this WhatsApp group chat and provide a {summary_mode.lower()}.
Focus on: key discussions, decisions made, important announcements, action items.

Chat messages:
{context}"""

            with st.spinner("🤖 Claude is thinking..."):
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )
                st.markdown("### 🤖 AI Summary")
                st.markdown(response.content[0].text)
        except ImportError:
            st.error("Install: `pip install anthropic`")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    elif provider == "🏠 Local Ollama":
        try:
            import requests

            prompt = f"""Analyze this WhatsApp group chat and provide a {summary_mode.lower()}.
Focus on: key discussions, decisions made, important announcements, action items.

Chat messages:
{context}"""

            with st.spinner("🤖 Ollama is thinking..."):
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "llama3.2", "prompt": prompt, "stream": False},
                    timeout=120,
                )
                st.markdown("### 🤖 AI Summary")
                st.markdown(response.json()['response'])
        except Exception as e:
            st.error(f"Ensure Ollama is running: `ollama serve` — Error: {str(e)}")

# ── CHAT CONTEXT PREVIEW ────────────────────────────────────────────────────
st.divider()
with st.expander("👁️ Preview Chat Context (what AI will see)"):
    st.text(context[:5000] + "..." if len(context) > 5000 else context)

# ── EXPORT ───────────────────────────────────────────────────────────────────
with st.expander("📥 Export Filtered Messages"):
    export_df = user_msgs[['date', 'user', 'message']].copy()
    export_buttons(export_df, "summary_export", f"chat_{start_date}_to_{end_date}")
