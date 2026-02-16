"""
📇 Member Directory
====================
Auto-extracted member profiles: Name, Location, LinkedIn URL.
"""

import streamlit as st
import pandas as pd
from utils.parser import extract_member_directory
from utils.helpers import export_buttons

st.set_page_config(page_title="Directory", page_icon="📇", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("⬅️ Please upload a chat file on the main page first.")
    st.stop()

df = st.session_state.df.copy()

st.markdown("## 📇 Member Directory")
st.caption("Auto-extracted from self-introduction messages (Nama / Alamat / LinkedIn)")

# ── EXTRACT MEMBERS ──────────────────────────────────────────────────────────
@st.cache_data
def get_directory(_df):
    return extract_member_directory(_df)

members = get_directory(df)

if members.empty:
    st.info("No structured introductions found (Nama + Alamat/LinkedIn pattern)")
    st.stop()

# ── KPI ROW ──────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📇 Verified Members", len(members))
with col2:
    st.metric("🔗 LinkedIn Profiles", (members['linkedin'] != '').sum())
with col3:
    st.metric("📍 With Location", (members['alamat'] != '').sum())
with col4:
    total_users = df[~df['is_system']]['user'].nunique()
    st.metric("👻 Unverified", total_users - len(members))

st.divider()

# ── SEARCH & FILTER ──────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    search = st.text_input("🔍 Search members (name, location, etc.)",
                            key="dir_search", placeholder="Type to search...")

with col2:
    filter_linkedin = st.checkbox("Only with LinkedIn", key="dir_linkedin")

# Apply filters
display = members.copy()
if search:
    mask = (
        display['nama'].str.contains(search, case=False, na=False) |
        display['alamat'].str.contains(search, case=False, na=False) |
        display['wa_name'].str.contains(search, case=False, na=False)
    )
    display = display[mask]

if filter_linkedin:
    display = display[display['linkedin'] != '']

st.markdown(f"Showing **{len(display)}** members")

# ── MEMBER TABLE ─────────────────────────────────────────────────────────────
table_df = display[['nama', 'alamat', 'linkedin', 'wa_name', 'date']].copy()
table_df.columns = ['Name', 'Location', 'LinkedIn', 'WA Name', 'Joined']

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        'LinkedIn': st.column_config.LinkColumn("LinkedIn", display_text="🔗 Open Profile"),
        'Joined': st.column_config.DateColumn("Joined", format="DD/MM/YY"),
    },
    height=min(700, len(table_df) * 38 + 40),
)

st.divider()

# ── LOCATION DISTRIBUTION ───────────────────────────────────────────────────
st.markdown("### 📍 Member Locations")

locations = display[display['alamat'] != '']['alamat'].str.strip().str.title()
loc_counts = locations.value_counts().head(20).reset_index()
loc_counts.columns = ['City', 'Members']

if not loc_counts.empty:
    import plotly.express as px
    from utils.helpers import apply_chart_theme

    fig = px.bar(loc_counts, x='Members', y='City', orientation='h',
                 color_discrete_sequence=['#10b981'],
                 text='Members')
    fig.update_traces(textposition='outside', textfont_size=11)
    apply_chart_theme(fig)
    fig.update_layout(
        height=max(350, len(loc_counts) * 28),
        yaxis=dict(autorange="reversed", title=""),
        xaxis_title="Members",
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── UNVERIFIED LIST ──────────────────────────────────────────────────────────
with st.expander("👻 Unverified Members (no intro posted)"):
    all_users = set(df[~df['is_system']]['user'].unique())
    verified = set(members['wa_name'].unique())
    unverified = sorted(all_users - verified)

    if unverified:
        unv_df = pd.DataFrame({'User': unverified})
        st.dataframe(unv_df, use_container_width=True, hide_index=True,
                      height=min(400, len(unv_df) * 38 + 40))
        st.markdown(f"**{len(unverified)}** users have not posted an introduction.")
    else:
        st.success("All active users have posted introductions!")

# ── EXPORT ───────────────────────────────────────────────────────────────────
st.divider()
with st.expander("📥 Export Member Directory"):
    export_buttons(display, "directory", "member_directory")
