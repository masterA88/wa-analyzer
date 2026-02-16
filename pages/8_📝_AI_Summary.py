"""
📝 AI Chat Summary
===================
LLM-powered summarization with multiple FREE AI providers.

Free providers (no credit card needed):
- Google Gemini Flash    → 250 req/day free
- Groq (Llama 4)        → 1,000 req/day free
- HuggingFace Inference  → 1,000 req/day free
- OpenRouter (free models)→ varies
- Local Ollama           → unlimited
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
st.caption("Summarize group conversations using free AI models — no credit card required")

# ── DATE RANGE SELECTOR ─────────────────────────────────────────────────────
st.markdown("### 🗓️ Select Time Range to Summarize")
filtered, start_date, end_date = date_range_filter(df, "summary")

user_msgs = filtered[~filtered['is_system'] & (filtered['user'] != 'system')]

col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    st.metric("💬 Messages", f"{len(user_msgs):,}")
with col_info2:
    st.metric("👥 Users", f"{user_msgs['user'].nunique()}")
with col_info3:
    st.metric("📅 Days", f"{user_msgs['date'].nunique()}")

st.divider()

# ── SUMMARY OPTIONS ──────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    summary_mode = st.selectbox("📋 Summary Mode:", [
        "Quick Summary (1 paragraph)",
        "Detailed Summary (key points)",
        "Key Decisions & Announcements",
        "Topic-Filtered Summary",
        "Daily Digest",
        "User Contribution Summary",
    ], key="summary_mode")

with col2:
    language = st.selectbox("🌐 Output Language:", [
        "Bahasa Indonesia",
        "English",
        "Auto (match chat language)",
    ], key="summary_lang")

with col3:
    if summary_mode == "Topic-Filtered Summary":
        topic_filter = st.text_input("🔍 Filter keyword:",
                                      placeholder="e.g., SQL, loker, interview",
                                      key="summary_topic")
    elif summary_mode == "User Contribution Summary":
        top_users_list = user_msgs['user'].value_counts().head(30).index.tolist()
        topic_filter = st.selectbox("👤 Select user:", top_users_list, key="summary_user")
    else:
        topic_filter = None

st.divider()

# ── AI PROVIDER CONFIGURATION ────────────────────────────────────────────────
st.markdown("### 🤖 AI Provider")

PROVIDERS = {
    "none": {
        "name": "📊 Rule-Based (No AI needed)",
        "free_tier": "Statistical summary — always available, no setup",
        "signup_url": None,
        "needs_key": False,
    },
    "gemini": {
        "name": "🟢 Google Gemini Flash",
        "free_tier": "250 req/day — no credit card — best quality",
        "signup_url": "https://aistudio.google.com/apikey",
        "needs_key": True,
    },
    "groq": {
        "name": "🟣 Groq (Llama 3.3 70B)",
        "free_tier": "1,000 req/day — fastest inference in the world",
        "signup_url": "https://console.groq.com/keys",
        "needs_key": True,
    },
    "huggingface": {
        "name": "🟡 HuggingFace Inference",
        "free_tier": "1,000 req/day — many open-source models",
        "signup_url": "https://huggingface.co/settings/tokens",
        "needs_key": True,
    },
    "openrouter": {
        "name": "🔵 OpenRouter (Free Models)",
        "free_tier": "Free tier models — multi-provider gateway",
        "signup_url": "https://openrouter.ai/keys",
        "needs_key": True,
    },
    "ollama": {
        "name": "🏠 Ollama (Local - Unlimited)",
        "free_tier": "100% free — runs on your machine — no limits",
        "signup_url": "https://ollama.ai",
        "needs_key": False,
    },
}

provider_keys = list(PROVIDERS.keys())
provider_labels = [f"{PROVIDERS[k]['name']}  —  {PROVIDERS[k]['free_tier']}" for k in provider_keys]

selected_idx = st.radio(
    "Choose provider:",
    range(len(provider_keys)),
    format_func=lambda i: provider_labels[i],
    key="ai_provider_radio",
    index=0,
)
provider_key = provider_keys[selected_idx]
provider = PROVIDERS[provider_key]

# API Key input
api_key = None
if provider["needs_key"]:
    col_key, col_link = st.columns([3, 1])
    with col_key:
        api_key = st.text_input(
            f"🔑 API Key:",
            type="password",
            key="ai_key",
            help="Session only — never stored anywhere",
            placeholder="Paste your API key here...",
        )
    with col_link:
        st.markdown("")
        st.markdown("")
        if provider["signup_url"]:
            st.link_button("Get free key →", provider["signup_url"], use_container_width=True)

    if not api_key:
        st.warning(f"⬆️ Paste your API key. [Get one free here]({provider['signup_url']})")

# Ollama config
ollama_model = "llama3.2"
if provider_key == "ollama":
    col_m, col_h = st.columns([2, 1])
    with col_m:
        ollama_model = st.text_input("Ollama model:", value="llama3.2", key="ollama_model")
    with col_h:
        st.markdown("")
        st.markdown("")
        st.caption("Run `ollama serve` first")


# ── PREPARE CONTEXT ──────────────────────────────────────────────────────────
def prepare_summary_context(msgs_df, max_chars=15000):
    """Prepare chat messages for LLM summarization."""
    if summary_mode == "Topic-Filtered Summary" and topic_filter:
        msgs_df = msgs_df[msgs_df['message'].str.contains(topic_filter, case=False, na=False)]
    elif summary_mode == "User Contribution Summary" and topic_filter:
        msgs_df = msgs_df[msgs_df['user'] == topic_filter]

    lines = []
    for _, row in msgs_df.iterrows():
        msg = row['message'][:300]
        if any(skip in msg for skip in ['omitted', 'deleted', 'encrypted']):
            continue
        lines.append(f"[{row['date']}] {row['user']}: {msg}")

    text = '\n'.join(lines)
    if len(text) > max_chars:
        quarter = max_chars // 4
        text = (text[:quarter] +
                f"\n\n... [{len(lines)} total messages, showing beginning and end] ...\n\n" +
                text[-quarter * 3:])

    return text, len(lines)


context, msg_count = prepare_summary_context(user_msgs)


def build_prompt():
    """Build the LLM prompt based on user selections."""
    lang_map = {
        "Bahasa Indonesia": "Respond entirely in Bahasa Indonesia.",
        "English": "Respond entirely in English.",
        "Auto (match chat language)": "Respond in the same language used most in the chat.",
    }

    mode_map = {
        "Quick Summary (1 paragraph)": "Write a concise 1-paragraph summary of the main topics and activities.",
        "Detailed Summary (key points)": "Provide a detailed summary with key points, organized by topic. Use headers and bullet points.",
        "Key Decisions & Announcements": "Extract only: 1) Key decisions made, 2) Important announcements, 3) Action items assigned. Skip casual/social chat.",
        "Topic-Filtered Summary": f"Summarize only discussions related to '{topic_filter}'. Ignore unrelated messages.",
        "Daily Digest": "Create a day-by-day digest showing what happened each day. Be concise per day.",
        "User Contribution Summary": f"Summarize what user '{topic_filter}' contributed: their key messages, topics they discussed, questions they asked, and resources they shared.",
    }

    return f"""You are analyzing a WhatsApp group chat export. {lang_map[language]}

Task: {mode_map[summary_mode]}

Context:
- Time period: {start_date} to {end_date}
- Total messages in range: {len(user_msgs):,}
- Active users: {user_msgs['user'].nunique()}
- Messages included below: {msg_count}

Chat messages:
{context}

Provide a clear, well-structured summary. Focus on substance, not small talk."""


# ── GENERATE SUMMARY ─────────────────────────────────────────────────────────
st.divider()

if st.button("🚀 Generate Summary", type="primary", use_container_width=True):

    # ── RULE-BASED ───────────────────────────────────────────────────────
    if provider_key == "none":
        st.markdown("### 📊 Statistical Summary")

        total = len(user_msgs)
        top_users = user_msgs['user'].value_counts().head(5)
        active_days = user_msgs['date'].nunique()

        from utils.parser import analyze_topics, extract_urls

        topics = analyze_topics(filtered)
        top_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]

        summary_text = f"**📅 Period:** {start_date} to {end_date} ({active_days} active days)\n\n"
        summary_text += f"**📊 Activity:** {total:,} messages from {user_msgs['user'].nunique()} users (avg {total // max(active_days, 1)}/day)\n\n"

        summary_text += "**🏆 Most Active Users:**\n"
        for i, (user, count) in enumerate(top_users.items()):
            summary_text += f"{i+1}. **{user}** — {count:,} messages ({count/total*100:.1f}%)\n"

        summary_text += "\n**🔥 Hot Topics:**\n"
        for topic, count in top_topics:
            if count > 0:
                summary_text += f"- **{topic}**: {count} mentions\n"

        urls = extract_urls(filtered)
        if not urls.empty:
            summary_text += f"\n**🔗 Links Shared:** {len(urls)} URLs from {urls['domain'].nunique()} domains\n"

        busiest = user_msgs.groupby('date').size()
        if not busiest.empty:
            summary_text += f"\n**📈 Busiest Day:** {busiest.idxmax()} ({busiest.max()} messages)"

        st.markdown(summary_text)
        st.session_state['last_summary'] = summary_text
        st.info("💡 For AI-powered natural language summaries, select a free AI provider above.")

    # ── GOOGLE GEMINI ────────────────────────────────────────────────────
    elif provider_key == "gemini":
        if not api_key:
            st.error("Please enter your Gemini API key.")
            st.stop()
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            with st.spinner("🟢 Gemini is analyzing your chat..."):
                response = model.generate_content(
                    build_prompt(),
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=3000,
                        temperature=0.3,
                    ),
                )
                st.markdown("### 🤖 AI Summary — Gemini Flash")
                st.markdown(response.text)
                st.session_state['last_summary'] = response.text
        except ImportError:
            st.error("❌ Install: `pip install google-generativeai` then add to requirements.txt")
        except Exception as e:
            st.error(f"❌ Gemini Error: {str(e)}")

    # ── GROQ ─────────────────────────────────────────────────────────────
    elif provider_key == "groq":
        if not api_key:
            st.error("Please enter your Groq API key.")
            st.stop()
        try:
            from groq import Groq
            client = Groq(api_key=api_key)

            with st.spinner("🟣 Groq is analyzing (this is fast)..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an expert community analyst who summarizes WhatsApp group discussions."},
                        {"role": "user", "content": build_prompt()},
                    ],
                    max_tokens=3000,
                    temperature=0.3,
                )
                st.markdown("### 🤖 AI Summary — Groq (Llama 3.3 70B)")
                st.markdown(response.choices[0].message.content)
                st.session_state['last_summary'] = response.choices[0].message.content
        except ImportError:
            st.error("❌ Install: `pip install groq` then add to requirements.txt")
        except Exception as e:
            st.error(f"❌ Groq Error: {str(e)}")

    # ── HUGGINGFACE ──────────────────────────────────────────────────────
    elif provider_key == "huggingface":
        if not api_key:
            st.error("Please enter your HuggingFace token.")
            st.stop()
        try:
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=api_key)

            with st.spinner("🟡 HuggingFace is analyzing your chat..."):
                messages = [
                    {"role": "system", "content": "You are an expert community analyst."},
                    {"role": "user", "content": build_prompt()},
                ]
                response = client.chat_completion(
                    model="mistralai/Mistral-7B-Instruct-v0.3",
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.3,
                )
                result = response.choices[0].message.content
                st.markdown("### 🤖 AI Summary — HuggingFace (Mistral 7B)")
                st.markdown(result)
                st.session_state['last_summary'] = result
        except ImportError:
            st.error("❌ Install: `pip install huggingface_hub` then add to requirements.txt")
        except Exception as e:
            st.error(f"❌ HuggingFace Error: {str(e)}")

    # ── OPENROUTER ───────────────────────────────────────────────────────
    elif provider_key == "openrouter":
        if not api_key:
            st.error("Please enter your OpenRouter API key.")
            st.stop()
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )

            with st.spinner("🔵 OpenRouter is analyzing your chat..."):
                response = client.chat.completions.create(
                    model="meta-llama/llama-3.3-70b-instruct:free",
                    messages=[
                        {"role": "system", "content": "You are an expert community analyst."},
                        {"role": "user", "content": build_prompt()},
                    ],
                    max_tokens=3000,
                    temperature=0.3,
                )
                st.markdown("### 🤖 AI Summary — OpenRouter (Free)")
                st.markdown(response.choices[0].message.content)
                st.session_state['last_summary'] = response.choices[0].message.content
        except ImportError:
            st.error("❌ Install: `pip install openai` then add to requirements.txt")
        except Exception as e:
            st.error(f"❌ OpenRouter Error: {str(e)}")

    # ── OLLAMA ───────────────────────────────────────────────────────────
    elif provider_key == "ollama":
        try:
            import requests as req

            with st.spinner(f"🏠 Ollama ({ollama_model}) analyzing locally..."):
                resp = req.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": ollama_model,
                        "messages": [
                            {"role": "system", "content": "You are an expert community analyst."},
                            {"role": "user", "content": build_prompt()},
                        ],
                        "stream": False,
                        "options": {"temperature": 0.3, "num_predict": 3000},
                    },
                    timeout=180,
                )
                if resp.status_code == 200:
                    result = resp.json()['message']['content']
                    st.markdown(f"### 🤖 AI Summary — Ollama ({ollama_model})")
                    st.markdown(result)
                    st.session_state['last_summary'] = result
                else:
                    st.error(f"Ollama error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"❌ Cannot connect to Ollama.\n\n"
                     f"Make sure it's running:\n"
                     f"```\nollama serve\nollama pull {ollama_model}\n```\n\n"
                     f"Error: {str(e)}")


# ── DOWNLOAD SUMMARY ─────────────────────────────────────────────────────────
if st.session_state.get('last_summary'):
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📥 Download Summary (.txt)",
            data=st.session_state['last_summary'],
            file_name=f"summary_{start_date}_to_{end_date}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col2:
        md = f"# Chat Summary\n**Period:** {start_date} to {end_date}\n\n{st.session_state['last_summary']}"
        st.download_button(
            "📥 Download Summary (.md)",
            data=md,
            file_name=f"summary_{start_date}_to_{end_date}.md",
            mime="text/markdown",
            use_container_width=True,
        )

# ── CONTEXT PREVIEW ──────────────────────────────────────────────────────────
st.divider()
with st.expander(f"👁️ Preview Context ({msg_count} messages prepared for AI)"):
    st.text(context[:5000] + "\n..." if len(context) > 5000 else context)

with st.expander("📥 Export Filtered Messages"):
    export_df = user_msgs[['date', 'user', 'message']].copy()
    export_buttons(export_df, "summary_export", f"chat_{start_date}_to_{end_date}")

# ── PROVIDER COMPARISON ──────────────────────────────────────────────────────
with st.expander("📊 Compare Free AI Providers"):
    st.markdown("""
| Provider | Free Limit | Speed | Quality | Credit Card |
|----------|-----------|-------|---------|-------------|
| **Gemini Flash** | 250 req/day | ⚡ Fast | ⭐⭐⭐⭐⭐ | ❌ Not needed |
| **Groq (Llama 3.3)** | 1,000 req/day | ⚡⚡ Fastest | ⭐⭐⭐⭐ | ❌ Not needed |
| **HuggingFace** | 1,000 req/day | 🐌 Slower | ⭐⭐⭐ | ❌ Not needed |
| **OpenRouter** | Varies | ⚡ Fast | ⭐⭐⭐⭐ | ❌ Not needed |
| **Ollama** | ♾️ Unlimited | 💻 Your HW | ⭐⭐⭐⭐ | ❌ Not needed |

**🏆 Recommendation:** Start with **Groq** (fastest + most generous free tier)
    """)
