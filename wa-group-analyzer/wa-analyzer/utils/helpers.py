"""
Shared Helper Utilities
=======================
Export functions, formatters, and reusable Streamlit components.
All free libraries - no paid dependencies.
"""

import io
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st


# ── EXPORT FUNCTIONS ─────────────────────────────────────────────────────────

def df_to_csv(df):
    """Convert DataFrame to CSV bytes for download."""
    return df.to_csv(index=False).encode('utf-8')


def df_to_excel(df, sheet_name='Sheet1'):
    """Convert DataFrame to Excel bytes for download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


def fig_to_image(fig, format='png'):
    """Convert Plotly figure to image bytes."""
    return fig.to_image(format=format, width=1200, height=600, scale=2)


def export_buttons(df, key_prefix, label="data"):
    """Render CSV + Excel download buttons side by side."""
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            f"📥 Download CSV",
            data=df_to_csv(df),
            file_name=f"{label}.csv",
            mime="text/csv",
            key=f"{key_prefix}_csv",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            f"📥 Download Excel",
            data=df_to_excel(df),
            file_name=f"{label}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"{key_prefix}_excel",
            use_container_width=True,
        )


# ── FORMATTING ───────────────────────────────────────────────────────────────

def format_number(n):
    """Format large numbers with K/M suffix."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def truncate(text, max_len=50):
    """Truncate text with ellipsis."""
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


# ── CHART THEME ──────────────────────────────────────────────────────────────

CHART_COLORS = [
    '#10b981', '#0ea5e9', '#8b5cf6', '#f59e0b', '#ef4444',
    '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#6366f1',
    '#14b8a6', '#a855f7', '#eab308', '#3b82f6', '#22c55e',
]

CHART_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, sans-serif', color='#94a3b8', size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor='rgba(148,163,184,0.1)', zerolinecolor='rgba(148,163,184,0.1)'),
    yaxis=dict(gridcolor='rgba(148,163,184,0.1)', zerolinecolor='rgba(148,163,184,0.1)'),
    hoverlabel=dict(bgcolor='#1e293b', font_size=12, font_color='#e2e8f0'),
)


def apply_chart_theme(fig):
    """Apply consistent dark theme to Plotly figure."""
    fig.update_layout(**CHART_LAYOUT)
    return fig


# ── METRIC CARD ──────────────────────────────────────────────────────────────

def metric_card(label, value, icon="📊", delta=None):
    """Render a styled metric card using Streamlit markdown."""
    delta_html = ""
    if delta is not None:
        color = "#10b981" if delta >= 0 else "#ef4444"
        arrow = "↑" if delta >= 0 else "↓"
        delta_html = f'<span style="color:{color}; font-size:12px;">{arrow} {abs(delta):.1f}%</span>'

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #111827 0%, #1e293b 100%);
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
    ">
        <div style="font-size: 22px; margin-bottom: 4px;">{icon}</div>
        <div style="font-size: 24px; font-weight: 700; color: #f1f5f9;">{value}</div>
        <div style="font-size: 12px; color: #64748b; margin-top: 4px;">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ── DATE RANGE FILTER ────────────────────────────────────────────────────────

def date_range_filter(df, key_prefix="global"):
    """Render date range filter and return filtered DataFrame."""
    min_date = df['date'].min()
    max_date = df['date'].max()

    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("From", value=min_date, min_value=min_date,
                              max_value=max_date, key=f"{key_prefix}_start")
    with col2:
        end = st.date_input("To", value=max_date, min_value=min_date,
                            max_value=max_date, key=f"{key_prefix}_end")

    filtered = df[(df['date'] >= start) & (df['date'] <= end)]
    return filtered, start, end


# ── USER FILTER ──────────────────────────────────────────────────────────────

def user_filter(df, key="user_filter"):
    """Multi-select user filter."""
    users = sorted(df[~df['is_system']]['user'].unique())
    selected = st.multiselect("Filter by users", users, key=key)
    if selected:
        return df[df['user'].isin(selected)]
    return df


# ── INDONESIAN STOPWORDS ─────────────────────────────────────────────────────

STOPWORDS_ID = {
    'yang', 'dan', 'di', 'ini', 'itu', 'dengan', 'untuk', 'dari', 'pada',
    'adalah', 'ke', 'ada', 'juga', 'tidak', 'akan', 'bisa', 'sudah', 'saya',
    'apa', 'kalau', 'tapi', 'udah', 'gak', 'aja', 'dulu', 'sih', 'lagi',
    'banget', 'kalo', 'buat', 'sama', 'terus', 'cuma', 'masih', 'jadi',
    'biar', 'kayak', 'karena', 'gimana', 'kalian', 'semua', 'pake', 'dong',
    'kan', 'kok', 'deh', 'yah', 'gitu', 'mau', 'kita', 'mas', 'kak',
    'mbak', 'pak', 'bang', 'bro', 'nih', 'nya', 'loh', 'wkwk', 'wkwkwk',
    'haha', 'hehe', 'hihi', 'ya', 'yg', 'ga', 'gk', 'lg', 'tp', 'sm',
    'the', 'and', 'is', 'to', 'of', 'in', 'for', 'that', 'this', 'with',
    'you', 'are', 'was', 'have', 'has', 'had', 'not', 'but', 'they',
    'image', 'omitted', 'sticker', 'video', 'message', 'edited', 'deleted',
}

STOPWORDS_EN = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her',
    'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there',
    'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get',
    'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no',
    'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your',
    'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then',
    'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
}

ALL_STOPWORDS = STOPWORDS_ID | STOPWORDS_EN
