"""
💬 Real Chat
=============
Tampilkan ulang chat WhatsApp seperti tampilan aslinya —
urutan kronologis, nama pengirim, dan waktu yang jelas.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from utils.helpers import export_buttons

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
        show_media  = st.checkbox("Tampilkan media omitted", value=True,  key="rc_media")

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

# ── TABS ──────────────────────────────────────────────────────────────────────

tab_chat, tab_table, tab_export = st.tabs(["💬 Chat View", "📋 Tabel", "📥 Export"])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT VIEW
# Menggunakan components.v1.html (iframe) bukan st.markdown unsafe_allow_html,
# karena st.markdown sering truncate/escape HTML kompleks → raw HTML tampil.
# ════════════════════════════════════════════════════════════════════════════

with tab_chat:

    if filtered.empty:
        st.info("Tidak ada pesan yang cocok dengan filter.")
    else:
        # ── Pagination ──────────────────────────────────────────────────────
        MESSAGES_PER_PAGE = 100
        total_pages = max(1, (len(filtered) - 1) // MESSAGES_PER_PAGE + 1)

        col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
        with col_p2:
            page_num = st.number_input(
                f"Halaman (1 – {total_pages})",
                min_value=1, max_value=total_pages, value=1, step=1,
                key="rc_page",
            )

        page_start = (page_num - 1) * MESSAGES_PER_PAGE
        page_end   = page_start + MESSAGES_PER_PAGE
        page_df    = filtered.iloc[page_start:page_end]

        st.caption(
            f"Menampilkan pesan {page_start + 1}–{min(page_end, len(filtered))} "
            f"dari {len(filtered):,}"
        )

        # ── Color palette per user ──────────────────────────────────────────
        BUBBLE_COLORS = [
            "#DCF8C6", "#FFF9C4", "#E1F5FE", "#F3E5F5", "#FBE9E7",
            "#E8F5E9", "#FCE4EC", "#E3F2FD", "#FFF3E0", "#E0F2F1",
        ]
        NAME_COLORS = [
            "#1B5E20", "#F57F17", "#01579B", "#4A148C", "#BF360C",
            "#2E7D32", "#880E4F", "#0D47A1", "#E65100", "#004D40",
        ]
        all_users     = sorted(df[~df["is_system"]]["user"].unique())
        user_bg_map   = {u: BUBBLE_COLORS[i % len(BUBBLE_COLORS)] for i, u in enumerate(all_users)}
        user_name_map = {u: NAME_COLORS[i  % len(NAME_COLORS)]    for i, u in enumerate(all_users)}

        # ── Helper: HTML-escape ─────────────────────────────────────────────
        def esc(s):
            return (str(s)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;"))

        # ── Build standalone HTML document ──────────────────────────────────
        rows_html = []
        prev_date = None

        for _, row in page_df.iterrows():
            # Date divider
            if row["date"] != prev_date:
                label = pd.Timestamp(row["date"]).strftime("%A, %d %B %Y")
                rows_html.append(
                    f'<div class="date-divider"><span>{esc(label)}</span></div>'
                )
                prev_date = row["date"]

            time_str = str(row["time"])[:5]

            # System message
            if row["is_system"]:
                rows_html.append(
                    f'<div class="system-msg">🔔 {esc(row["message"])} · {time_str}</div>'
                )
                continue

            user     = str(row["user"])
            bg       = user_bg_map.get(user, "#F0F4F8")
            nc       = user_name_map.get(user, "#1a365d")
            msg_raw  = esc(row["message"])
            is_media = bool(row.get("is_media", False))
            msg_html = (
                f'<span class="msg-media">📎 {msg_raw}</span>'
                if is_media else msg_raw
            )

            rows_html.append(
                f'<div class="bubble-row">'
                f'<div class="bubble" style="background:{bg};">'
                f'<div class="sender-name" style="color:{nc};">{esc(user)}</div>'
                f'<div class="msg-text">{msg_html}</div>'
                f'<div class="msg-time">{time_str}</div>'
                f'</div></div>'
            )

        full_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #0f172a;
    padding: 12px 8px 24px;
  }}
  .date-divider {{
    text-align: center;
    margin: 16px 0 8px;
  }}
  .date-divider span {{
    background: #1e293b;
    color: #94a3b8;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 14px;
    border-radius: 20px;
    border: 1px solid #334155;
  }}
  .bubble-row {{
    display: flex;
    margin-bottom: 6px;
  }}
  .bubble {{
    max-width: 78%;
    border-radius: 0px 12px 12px 12px;
    padding: 7px 11px 5px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.25);
    word-break: break-word;
  }}
  .sender-name {{
    font-size: 11.5px;
    font-weight: 700;
    margin-bottom: 3px;
  }}
  .msg-text {{
    font-size: 13.5px;
    color: #1a202c;
    line-height: 1.5;
    white-space: pre-wrap;
  }}
  .msg-time {{
    font-size: 10px;
    color: #475569;
    text-align: right;
    margin-top: 3px;
  }}
  .msg-media {{
    font-style: italic;
    color: #64748b;
  }}
  .system-msg {{
    text-align: center;
    color: #64748b;
    font-size: 11px;
    font-style: italic;
    margin: 6px auto;
    padding: 3px 14px;
    background: #1e293b;
    border-radius: 12px;
    display: table;
  }}
</style>
</head>
<body>
{content}
</body>
</html>""".format(content="\n".join(rows_html))

        # Render inside iframe — height scales with message count
        iframe_height = min(4000, max(500, len(page_df) * 72))
        components.html(full_html, height=iframe_height, scrolling=True)

        st.caption(
            f"Halaman {page_num} dari {total_pages} · {MESSAGES_PER_PAGE} pesan/halaman"
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
        display_df["date"]     = display_df["date"].astype(str)
        display_df["time"]     = display_df["time"].astype(str).str[:5]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=600,
            column_config={
                "datetime": st.column_config.TextColumn("Waktu",   width="medium"),
                "date":     st.column_config.TextColumn("Tanggal", width="small"),
                "time":     st.column_config.TextColumn("Jam",     width="small"),
                "user":     st.column_config.TextColumn("Nama",    width="medium"),
                "message":  st.column_config.TextColumn("Pesan",   width="large"),
                "msg_type": st.column_config.TextColumn("Tipe",    width="small"),
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
            f"Export **{len(filtered):,} pesan** sesuai filter aktif "
            f"({start_date} s/d {end_date})"
            + (f", pengirim: {', '.join(selected_users)}" if selected_users else ", semua pengirim")
        )

        export_df = filtered[
            ["datetime", "date", "time", "user", "message", "msg_type", "is_media", "is_system"]
        ].copy()
        export_df["datetime"] = export_df["datetime"].dt.strftime("%d/%m/%Y %H:%M:%S")
        export_df["date"]     = export_df["date"].astype(str)
        export_df["time"]     = export_df["time"].astype(str).str[:8]

        export_df.columns = [
            "Waktu", "Tanggal", "Jam", "Nama",
            "Pesan", "Tipe", "Is Media", "Is System"
        ]

        st.divider()
        export_buttons(export_df, "realchat_export", "real_chat")

        st.divider()
        st.markdown("#### 👁️ Preview data yang akan di-export")
        st.dataframe(export_df.head(20), use_container_width=True, hide_index=True)
        if len(export_df) > 20:
            st.caption(f"... dan {len(export_df) - 20:,} pesan lainnya")
