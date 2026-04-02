"""
💬 Real Chat
=============
Tampilkan ulang chat WhatsApp seperti tampilan aslinya —
urutan kronologis, nama pengirim, dan waktu yang jelas.
"""

import streamlit as st
import pandas as pd
from utils.helpers import export_buttons, df_to_csv, df_to_excel

st.set_page_config(page_title="Real Chat", page_icon="💬", layout="wide")

# ── GUARD ────────────────────────────────────────────────────────────────────

if "df" not in st.session_state or st.session_state.df is None:
    st.warning("⬅️ Please upload a chat file on the main page first.")
    st.stop()

df = st.session_state.df.copy()

st.markdown("## 💬 Real Chat")
st.caption("Baca ulang percakapan grup seperti tampilan WhatsApp asli.")

st.divider()

# ── FILTERS ──────────────────────────────────────────────────────────────────

with st.expander("🔧 Filter & Pengaturan", expanded=True):
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        users = sorted(df[~df["is_system"]]["user"].unique())
        selected_users = st.multiselect(
            "Filter pengirim:",
            options=users,
            default=[],
            placeholder="Semua pengirim",
            key="rc_users",
        )

    with col2:
        start_date = st.date_input(
            "Dari tanggal:",
            value=df["date"].min(),
            min_value=df["date"].min(),
            max_value=df["date"].max(),
            key="rc_start",
        )

    with col3:
        end_date = st.date_input(
            "Sampai tanggal:",
            value=df["date"].max(),
            min_value=df["date"].min(),
            max_value=df["date"].max(),
            key="rc_end",
        )

    with col4:
        show_system = st.checkbox("Tampilkan pesan sistem", value=False, key="rc_system")
        show_media = st.checkbox("Tampilkan media omitted", value=True, key="rc_media")

# ── APPLY FILTERS ─────────────────────────────────────────────────────────────

filtered = df[
    (df["date"] >= start_date) & (df["date"] <= end_date)
].copy()

if not show_system:
    filtered = filtered[~filtered["is_system"]]

if not show_media:
    filtered = filtered[~filtered["is_media"]]

if selected_users:
    filtered = filtered[filtered["user"].isin(selected_users)]

filtered = filtered.sort_values("datetime").reset_index(drop=True)

st.markdown(
    f"**{len(filtered):,} pesan** ditampilkan"
    + (f" dari {len(selected_users)} pengirim" if selected_users else "")
    + f" · {start_date} s/d {end_date}"
)

st.divider()

# ── TABS: Chat View & Table View ──────────────────────────────────────────────

tab_chat, tab_table, tab_export = st.tabs(["💬 Chat View", "📋 Tabel", "📥 Export"])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT VIEW (WA-style bubbles)
# ════════════════════════════════════════════════════════════════════════════

with tab_chat:

    if filtered.empty:
        st.info("Tidak ada pesan yang cocok dengan filter.")
        st.stop()

    # Pagination agar tidak lag kalau pesan ribuan
    MESSAGES_PER_PAGE = 100
    total_pages = max(1, (len(filtered) - 1) // MESSAGES_PER_PAGE + 1)

    col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
    with col_pag2:
        page_num = st.number_input(
            f"Halaman (1 – {total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key="rc_page",
        )

    page_start = (page_num - 1) * MESSAGES_PER_PAGE
    page_end = page_start + MESSAGES_PER_PAGE
    page_df = filtered.iloc[page_start:page_end]

    st.caption(
        f"Menampilkan pesan {page_start + 1}–{min(page_end, len(filtered))} "
        f"dari {len(filtered):,}"
    )

    # ── Color palette per user ──────────────────────────────────────────────
    # Assign warna berbeda untuk tiap pengirim (WA-style)
    BUBBLE_COLORS = [
        "#DCF8C6",  # hijau muda (default WA sent)
        "#FFF9C4",  # kuning muda
        "#E1F5FE",  # biru muda
        "#F3E5F5",  # ungu muda
        "#FBE9E7",  # oranye muda
        "#E8F5E9",  # hijau terang
        "#FCE4EC",  # pink muda
        "#E3F2FD",  # biru langit
        "#FFF3E0",  # peach
        "#E0F2F1",  # teal muda
    ]
    TEXT_COLORS = [
        "#1B5E20", "#F57F17", "#01579B", "#4A148C",
        "#BF360C", "#1B5E20", "#880E4F", "#0D47A1",
        "#E65100", "#004D40",
    ]

    all_users = sorted(df[~df["is_system"]]["user"].unique())
    user_color_map = {
        user: BUBBLE_COLORS[i % len(BUBBLE_COLORS)]
        for i, user in enumerate(all_users)
    }
    user_text_map = {
        user: TEXT_COLORS[i % len(TEXT_COLORS)]
        for i, user in enumerate(all_users)
    }

    # ── CSS ────────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .chat-wrapper {
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 12px 4px;
        font-family: 'Segoe UI', sans-serif;
    }
    .chat-date-divider {
        text-align: center;
        margin: 14px 0 6px;
    }
    .chat-date-divider span {
        background: #e2e8f0;
        color: #475569;
        font-size: 11px;
        padding: 3px 12px;
        border-radius: 20px;
        font-weight: 600;
    }
    .chat-bubble-row {
        display: flex;
        align-items: flex-end;
        gap: 8px;
        max-width: 80%;
    }
    .chat-bubble {
        border-radius: 12px 12px 12px 4px;
        padding: 8px 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.12);
        position: relative;
        word-break: break-word;
    }
    .chat-sender {
        font-size: 11px;
        font-weight: 700;
        margin-bottom: 3px;
    }
    .chat-text {
        font-size: 13.5px;
        color: #1a202c;
        line-height: 1.5;
        white-space: pre-wrap;
    }
    .chat-time {
        font-size: 10px;
        color: #64748b;
        text-align: right;
        margin-top: 4px;
    }
    .chat-system {
        text-align: center;
        color: #94a3b8;
        font-size: 11px;
        font-style: italic;
        margin: 4px 0;
    }
    .chat-media {
        font-style: italic;
        color: #64748b;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Render bubbles ─────────────────────────────────────────────────────
    html_parts = ['<div class="chat-wrapper">']
    prev_date = None

    for _, row in page_df.iterrows():
        # Date divider
        if row["date"] != prev_date:
            date_label = pd.Timestamp(row["date"]).strftime("%A, %d %B %Y")
            html_parts.append(
                f'<div class="chat-date-divider"><span>{date_label}</span></div>'
            )
            prev_date = row["date"]

        time_str = str(row["time"])[:5]  # HH:MM

        # System messages
        if row["is_system"]:
            msg_escaped = str(row["message"]).replace("<", "&lt;").replace(">", "&gt;")
            html_parts.append(
                f'<div class="chat-system">🔔 {msg_escaped} · {time_str}</div>'
            )
            continue

        user = str(row["user"])
        bg_color = user_color_map.get(user, "#F0F4F8")
        name_color = user_text_map.get(user, "#2D3748")

        msg_text = str(row["message"]).replace("<", "&lt;").replace(">", "&gt;")
        is_media_msg = row.get("is_media", False)

        msg_display = (
            f'<span class="chat-media">📎 {msg_text}</span>'
            if is_media_msg
            else msg_text
        )

        bubble_html = f"""
        <div class="chat-bubble-row">
            <div class="chat-bubble" style="background:{bg_color};">
                <div class="chat-sender" style="color:{name_color};">{user}</div>
                <div class="chat-text">{msg_display}</div>
                <div class="chat-time">{time_str}</div>
            </div>
        </div>
        """
        html_parts.append(bubble_html)

    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)

    # Bottom pagination
    st.divider()
    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b2:
        st.markdown(
            f"<div style='text-align:center; color:#64748b; font-size:12px;'>"
            f"Halaman {page_num} dari {total_pages} · "
            f"{MESSAGES_PER_PAGE} pesan per halaman</div>",
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — TABLE VIEW
# ════════════════════════════════════════════════════════════════════════════

with tab_table:

    if filtered.empty:
        st.info("Tidak ada pesan yang cocok dengan filter.")
    else:
        display_df = filtered[["datetime", "date", "time", "user", "message", "msg_type"]].copy()
        display_df["datetime"] = display_df["datetime"].dt.strftime("%d/%m/%Y %H:%M")
        display_df["date"] = display_df["date"].astype(str)
        display_df["time"] = display_df["time"].astype(str).str[:5]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=600,
            column_config={
                "datetime": st.column_config.TextColumn("Waktu", width="medium"),
                "date":     st.column_config.TextColumn("Tanggal", width="small"),
                "time":     st.column_config.TextColumn("Jam", width="small"),
                "user":     st.column_config.TextColumn("Pengirim", width="medium"),
                "message":  st.column_config.TextColumn("Pesan", width="large"),
                "msg_type": st.column_config.TextColumn("Tipe", width="small"),
            },
        )

        st.caption(f"Total: {len(display_df):,} pesan")


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — EXPORT
# ════════════════════════════════════════════════════════════════════════════

with tab_export:

    if filtered.empty:
        st.info("Tidak ada data untuk di-export.")
    else:
        st.markdown("### 📥 Export Riwayat Chat")
        st.caption(
            f"Export **{len(filtered):,} pesan** sesuai filter yang aktif "
            f"({start_date} s/d {end_date})"
            + (f", dari: {', '.join(selected_users)}" if selected_users else ", semua pengirim")
        )

        export_df = filtered[["datetime", "date", "time", "user", "message", "msg_type", "is_media", "is_system"]].copy()
        export_df["datetime"] = export_df["datetime"].dt.strftime("%d/%m/%Y %H:%M:%S")
        export_df["date"] = export_df["date"].astype(str)
        export_df["time"] = export_df["time"].astype(str).str[:8]

        export_df.columns = [
            "Datetime", "Tanggal", "Jam", "Pengirim",
            "Pesan", "Tipe", "Is Media", "Is System"
        ]

        st.divider()
        export_buttons(export_df, "realchat_export", "real_chat")

        st.divider()
        st.markdown("#### 👁️ Preview data yang akan di-export")
        st.dataframe(export_df.head(20), use_container_width=True, hide_index=True)
        if len(export_df) > 20:
            st.caption(f"... dan {len(export_df) - 20:,} pesan lainnya")
