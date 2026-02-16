"""
🕸️ Social Network Graph
=========================
Interaction network between group members.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.parser import build_interaction_network
from utils.helpers import apply_chart_theme, date_range_filter, export_buttons

st.set_page_config(page_title="Network", page_icon="🕸️", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("⬅️ Please upload a chat file on the main page first.")
    st.stop()

df = st.session_state.df.copy()

st.markdown("## 🕸️ Social Network Graph")
st.caption("Based on sequential message patterns — who talks after whom")

with st.expander("🗓️ Filter by Date Range", expanded=False):
    df, _, _ = date_range_filter(df, "network")

# ── SETTINGS ─────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    window = st.slider("Response window (minutes):", 1, 10, 3,
                        help="Max time gap to consider a reply",
                        key="net_window")
with col2:
    min_interactions = st.slider("Min interactions to show:", 1, 50, 5,
                                  key="net_min")
with col3:
    top_n_users = st.slider("Top N users to include:", 5, 50, 20,
                             key="net_top_n")

# ── BUILD NETWORK ────────────────────────────────────────────────────────────
@st.cache_data
def compute_network(_df, window_min):
    return build_interaction_network(_df, window_min)

with st.spinner("Building interaction network..."):
    edges = compute_network(df, window)

if not edges:
    st.info("No interactions found with current settings. Try increasing the window.")
    st.stop()

# Filter to top users
user_msgs = df[~df['is_system'] & (df['user'] != 'system')]
top_users = set(user_msgs['user'].value_counts().head(top_n_users).index)

filtered_edges = {
    edge: count for edge, count in edges.items()
    if count >= min_interactions
    and edge[0] in top_users
    and edge[1] in top_users
}

if not filtered_edges:
    st.info("No interactions meet the minimum threshold. Try lowering it.")
    st.stop()

# ── BUILD GRAPH WITH NETWORKX ────────────────────────────────────────────────
try:
    import networkx as nx

    G = nx.Graph()
    for (u, v), weight in filtered_edges.items():
        G.add_edge(u, v, weight=weight)

    # Compute metrics
    degree_cent = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)

    # Layout
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    # ── PLOTLY NETWORK ───────────────────────────────────────────────────────
    # Edges
    edge_x, edge_y = [], []
    edge_weights = []
    for u, v, d in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_weights.append(d['weight'])

    max_w = max(edge_weights) if edge_weights else 1

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='rgba(148,163,184,0.3)'),
        hoverinfo='none',
        mode='lines'
    )

    # Nodes
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    node_sizes = [10 + degree_cent[n] * 60 for n in G.nodes()]
    node_colors = [betweenness[n] for n in G.nodes()]
    node_text = [
        f"<b>{n}</b><br>"
        f"Connections: {G.degree(n)}<br>"
        f"Centrality: {degree_cent[n]:.3f}<br>"
        f"Betweenness: {betweenness[n]:.3f}"
        for n in G.nodes()
    ]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        hovertext=node_text,
        text=[n if degree_cent.get(n, 0) > 0.1 else '' for n in G.nodes()],
        textposition='top center',
        textfont=dict(size=9, color='#e2e8f0'),
        marker=dict(
            size=node_sizes,
            color=node_colors,
            colorscale=[[0, '#1e3a5f'], [0.5, '#10b981'], [1.0, '#f59e0b']],
            colorbar=dict(title="Betweenness", thickness=15),
            line=dict(width=1, color='#0f172a'),
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    apply_chart_theme(fig)
    fig.update_layout(
        height=600,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        title=f"Interaction Network ({G.number_of_nodes()} users, {G.number_of_edges()} connections)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── NETWORK METRICS ──────────────────────────────────────────────────────
    st.markdown("### 📊 Network Metrics")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔗 Nodes", G.number_of_nodes())
    with col2:
        st.metric("↔️ Edges", G.number_of_edges())
    with col3:
        density = nx.density(G)
        st.metric("📐 Density", f"{density:.3f}")
    with col4:
        if nx.is_connected(G):
            diameter = nx.diameter(G)
            st.metric("📏 Diameter", diameter)
        else:
            components = nx.number_connected_components(G)
            st.metric("🧩 Components", components)

    # Top influencers
    st.markdown("### 👑 Top Influencers")

    influence_df = pd.DataFrame({
        'User': list(G.nodes()),
        'Connections': [G.degree(n) for n in G.nodes()],
        'Degree Centrality': [round(degree_cent[n], 4) for n in G.nodes()],
        'Betweenness': [round(betweenness[n], 4) for n in G.nodes()],
        'Total Interactions': [
            sum(d['weight'] for _, _, d in G.edges(n, data=True))
            for n in G.nodes()
        ],
    }).sort_values('Total Interactions', ascending=False)

    st.dataframe(influence_df.head(20), use_container_width=True, hide_index=True)

    # ── EXPORT ───────────────────────────────────────────────────────────────
    st.divider()
    with st.expander("📥 Export Network Data"):
        export_buttons(influence_df, "network", "network_analysis")

        # Edge list
        st.markdown("##### Edge List")
        edge_df = pd.DataFrame([
            {'User A': u, 'User B': v, 'Interactions': d['weight']}
            for u, v, d in G.edges(data=True)
        ]).sort_values('Interactions', ascending=False)
        export_buttons(edge_df, "edges", "edge_list")

except ImportError:
    st.warning("Install `networkx` for network analysis: `pip install networkx`")
    st.markdown("##### Raw Interaction Data")
    edge_data = [
        {'User A': e[0], 'User B': e[1], 'Interactions': c}
        for e, c in sorted(filtered_edges.items(), key=lambda x: x[1], reverse=True)
    ]
    st.dataframe(pd.DataFrame(edge_data).head(50), use_container_width=True, hide_index=True)
