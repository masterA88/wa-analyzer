# 💬 WhatsApp Group Analyzer

> Transform WhatsApp chat exports into actionable community intelligence - 100% free and open-source. 


## Welcome! I'm Hilmi, the creator of this project. Explore the live application here:
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://wa-analyzer.streamlit.app/)


---

## 🚀 Quick Start

```bash
# 1. Clone / download the project
cd wa-analyzer

# 2. Install dependencies (all free)
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

Then upload your WhatsApp chat export (`.txt` or `.zip`) and explore!

---

## 📱 How to Export WhatsApp Chat

1. Open your WhatsApp group
2. Tap **⋮ More** → **Export Chat** → **Without Media**
3. Save the `.txt` or `.zip` file
4. Upload it to the app

---

## 📊 Features (10 Pages)

| Page | Feature | Description |
|------|---------|-------------|
| 📊 | **Overview Dashboard** | KPIs, trends, message volume, media breakdown |
| 🏆 | **User Leaderboard** | Top N selector, engagement tiers, activity heatmap |
| 📇 | **Member Directory** | Auto-extracted names, locations, LinkedIn profiles |
| ⏰ | **Temporal Analytics** | Hourly/daily/weekly patterns, calendar heatmap |
| 💬 | **Topics & Content** | Word cloud, topic tracking, shared resources |
| 😊 | **Emoji & Sentiment** | Emoji leaderboard, mood indicators, humor index |
| 🕸️ | **Social Network** | Interactive interaction graph, influencer metrics |
| 📝 | **AI Chat Summary** | LLM-powered summarization (plug any free API) |
| 🔍 | **Search Messages** | Full-text search with filters |
| 📥 | **Export Center** | CSV, Excel, JSON export for all data |

---

## 💰 Cost: $0

**Every single component is free:**

| Component | Library | License | Cost |
|-----------|---------|---------|------|
| Web Framework | Streamlit | Apache 2.0 | Free |
| Charts | Plotly | MIT | Free |
| Data Processing | Pandas, NumPy | BSD | Free |
| Word Clouds | wordcloud | MIT | Free |
| Network Analysis | NetworkX | BSD | Free |
| Emoji Processing | emoji | BSD | Free |
| Excel Export | openpyxl, xlsxwriter | MIT | Free |
| Hosting | Streamlit Cloud | — | Free tier |

**AI Summary (optional, all have free tiers):**

| Provider | Free Tier | How to Get |
|----------|-----------|-----------|
| Google Gemini | 15 req/min | [aistudio.google.com](https://aistudio.google.com) |
| Groq | Generous limits | [console.groq.com](https://console.groq.com) |
| Ollama (local) | Unlimited | [ollama.ai](https://ollama.ai) |
| OpenAI | $5 trial | [platform.openai.com](https://platform.openai.com) |

---

## 🏗️ Architecture

```
wa-analyzer/
├── app.py                      # Main entry — upload + routing
├── .streamlit/config.toml      # Theme configuration
├── pages/
│   ├── 1_📊_Overview.py
│   ├── 2_🏆_Leaderboard.py
│   ├── 3_📇_Directory.py
│   ├── 4_⏰_Temporal.py
│   ├── 5_💬_Topics.py
│   ├── 6_😊_Sentiment.py
│   ├── 7_🕸️_Network.py
│   ├── 8_📝_AI_Summary.py
│   ├── 9_🔍_Search.py
│   └── 10_📥_Export.py
├── utils/
│   ├── __init__.py
│   ├── parser.py               # WhatsApp format parser
│   └── helpers.py              # Shared utilities
├── assets/
│   └── style.css               # Custom theme
├── requirements.txt
└── README.md
```

---

## 🔌 Scaling Up — Future Add-ons

The modular architecture makes it easy to add:

| Feature | How | Effort |
|---------|-----|--------|
| **AI Summaries** | Uncomment AI provider in requirements.txt, add API key | 5 min |
| **Multi-group comparison** | Upload multiple files, store in DuckDB | Medium |
| **Authentication** | `streamlit-authenticator` package | Easy |
| **Scheduled reports** | Cron job + email via `smtplib` | Medium |
| **Database backend** | Replace DataFrames with DuckDB/SQLite | Medium |
| **Docker deployment** | Add Dockerfile (template below) | Easy |
| **Webhook alerts** | Add Telegram/Discord bot integration | Medium |

---


