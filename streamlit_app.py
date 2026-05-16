import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"

PLAYERS = ["MurzichAI", "axantroff", "trofimova2002"]

# Palette derived from in-game Minecraft block colors
PLAYER_COLOR = {
    "MurzichAI": "#DC2626",     # redstone
    "axantroff": "#3DD5F3",     # diamond
    "trofimova2002": "#7CB342", # grass top
}
CAT_COLOR = {
    "Mob": "#DC2626",          # redstone red — hostile mobs
    "Environment": "#FF8C1A",  # lava orange — environment hazards
    "PvP": "#3DD5F3",          # diamond cyan — player vs player
    "Other": "#9CA3AF",        # stone gray
}
ACCENT_GOLD = "#FFAA00"        # gold ingot
ACCENT_XP = "#A4FF00"          # XP green
GRASS_GREEN = "#7CB342"        # grass top
DIAMOND = "#3DD5F3"
BG_DARK = "#1B1D24"            # deep obsidian-ish dark
SURFACE = "#2A2D36"            # stone
BORDER = "#3D4148"
TEXT = "#F5F5F5"
MUTED = "#9CA3AF"

MOB_KEYWORDS = [
    "creeper","zombie","husk","skeleton","enderman","iron golem","piglin","ghast",
    "blaze","wolf","bear","drowned","wither","spider","witch","vex","phantom",
    "dragon","warden","vindicator","pillager","ravager","silverfish","endermite",
    "slime","magma cube","elder guardian","guardian","shulker",
]
ENV_KEYWORDS = [
    "fell","ground too hard","lava","fire","burn","flame","stalagmite","stalactite",
    "cactus","lightning","drown","froze","frozen","starve","suffocate","wither",
    "kinetic","crushed","squashed","bang","danger zone","wall","dehydration",
    "floor was lava",
]

# Icons (emoji-based since Streamlit renders them natively)
MOB_ICON = {
    "creeper": "🟢", "zombie": "🧟", "husk": "🧟", "skeleton": "💀",
    "enderman": "🟣", "iron golem": "🤖", "piglin": "🐷", "ghast": "👻",
    "blaze": "🔥", "wolf": "🐺", "bear": "🐻", "drowned": "🌊",
    "dragon": "🐉", "spider": "🕷️", "phantom": "🦇", "warden": "👹",
}
ENV_ICON = {
    "fell": "📉", "ground too hard": "📉", "lava": "🌋", "fire": "🔥",
    "burn": "🔥", "flame": "🔥", "stalagmite": "🦴", "stalactite": "🦴",
    "cactus": "🌵", "lightning": "⚡", "drown": "🌊", "froze": "❄️",
    "frozen": "❄️", "starve": "🍖", "suffocate": "🧱",
}


def categorize(msg: str) -> str:
    m = msg.lower()
    for p in PLAYERS:
        if f"by {p}" in msg:
            return "PvP"
    if any(k in m for k in MOB_KEYWORDS):
        return "Mob"
    if any(k in m for k in ENV_KEYWORDS):
        return "Environment"
    return "Other"


def message_icon(msg: str) -> str:
    m = msg.lower()
    for p in PLAYERS:
        if f"by {p}" in msg:
            return "⚔️"
    for k, ic in {**MOB_ICON, **ENV_ICON}.items():
        if k in m:
            return ic
    return "❓"


@st.cache_data
def load_data():
    summary = pd.read_csv(DATA_DIR / "summary.csv")
    worlds = pd.read_csv(DATA_DIR / "worlds.csv", parse_dates=["start_time", "first_death_at"])
    deaths = pd.read_csv(DATA_DIR / "deaths.csv", parse_dates=["timestamp"])
    death_messages = pd.read_csv(DATA_DIR / "death_messages.csv")
    players = pd.read_csv(DATA_DIR / "players.csv")
    pvp = pd.read_csv(DATA_DIR / "pvp.csv")

    death_messages["category"] = death_messages["death_message"].map(categorize)
    death_messages["icon"] = death_messages["death_message"].map(message_icon)
    worlds["first_death_category"] = worlds["first_death_message"].fillna("").map(
        lambda m: categorize(m) if m else None
    )
    return {
        "summary": dict(zip(summary["metric"], summary["value"])),
        "worlds": worlds,
        "deaths": deaths,
        "death_messages": death_messages,
        "players": players,
        "pvp": pvp,
    }


def metric_to_int(d: dict, key: str) -> int:
    return int(float(d[key]))


def section_header(title: str, sub: str = ""):
    st.markdown(f"### {title}")
    if sub:
        st.caption(sub)


def build_app():
    st.set_page_config(
        page_title="The Hardcore Chronicles",
        page_icon="⛏️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        f"""
        <style>
        .block-container {{ padding-top: 2rem; padding-bottom: 2rem; max-width: 1300px; }}
        h1 {{ color: {ACCENT_GOLD} !important; letter-spacing: 0.08em; text-align: center;
              text-shadow: 0 0 24px rgba(255,170,0,0.25); font-weight: 800; }}
        h2, h3 {{ color: {ACCENT_GOLD} !important; letter-spacing: 0.03em; font-weight: 700; }}
        div[data-testid="stMetricValue"] {{
            font-size: 3rem; color: {ACCENT_GOLD}; font-weight: 800;
            text-shadow: 0 0 12px rgba(255,170,0,0.2);
        }}
        div[data-testid="stMetricLabel"] {{ font-size: 1rem; color: {TEXT}; font-weight: 600; }}
        div[data-testid="stMetric"] {{
            background: {SURFACE};
            border: 2px solid {BORDER};
            border-radius: 6px;
            padding: 18px 16px;
        }}
        section[data-testid="stSidebar"] {{ background-color: {SURFACE}; }}
        .stPlotlyChart {{ background-color: transparent; }}
        .fun-fact {{
            background: {SURFACE};
            padding: 16px 20px;
            border-left: 5px solid {ACCENT_GOLD};
            border-radius: 4px;
            margin: 10px 0;
            font-size: 0.98rem;
            line-height: 1.55;
        }}
        .fun-fact b {{ color: {ACCENT_GOLD}; }}
        hr {{ border-color: {BORDER} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    data = load_data()
    s = data["summary"]

    # === Title ===
    st.markdown("# ⛏️ THE HARDCORE CHRONICLES")
    st.markdown(
        f"<p style='text-align:center;color:{MUTED};font-style:italic;margin-top:-10px;'>"
        f"A Minecraft journey  —  May 5 to May 16, 2026</p>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<hr style='border-color:{BORDER};'>", unsafe_allow_html=True)

    n_total = metric_to_int(s, "total_worlds_attempted")
    n_failed = metric_to_int(s, "worlds_failed")
    n_safe = metric_to_int(s, "worlds_survived_rerolled")
    survival = data["worlds"]["survival_minutes"].dropna().astype(float)
    total_hours = survival.sum() / 60

    # === Hero metrics ===
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌍  Worlds Attempted", n_total)
    c2.metric("💀  Ended in Death", n_failed)
    c3.metric("🔄  Rerolled (skipped)", n_safe)
    c4.metric("⏰  Total Lived", f"{total_hours:.0f} h")

    st.markdown("<br>", unsafe_allow_html=True)

    # === Row: How each run ended (wide) + What killed the runs (narrow) ===
    left, right = st.columns([2.2, 1])

    with left:
        section_header("☠️ How Each Run Ended", "First death per world — official Minecraft death message phrasing")

        dm = data["death_messages"].sort_values("count_first_deaths_only", ascending=True).copy()
        dm = dm[dm["count_first_deaths_only"] > 0]
        dm["label"] = dm.apply(
            lambda r: f"{r['icon']}  <player> {r['death_message']}", axis=1
        )

        fig = px.bar(
            dm,
            x="count_first_deaths_only",
            y="label",
            orientation="h",
            color="category",
            color_discrete_map=CAT_COLOR,
            text="count_first_deaths_only",
            hover_data={"category": True, "label": False, "count_first_deaths_only": False, "death_message": True},
            labels={"count_first_deaths_only": "Worlds ended this way", "label": ""},
            height=520,
        )
        fig.update_traces(
            textposition="outside",
            textfont=dict(size=14, color=TEXT),
            marker_line_color=BG_DARK,
            marker_line_width=2,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="monospace", color=TEXT, size=13),
            margin=dict(l=10, r=40, t=10, b=40),
            xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            legend=dict(
                title="Cause category",
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="right",
                x=1,
                bgcolor=SURFACE,
                bordercolor=BORDER,
                borderwidth=1,
                font=dict(color=TEXT),
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        section_header("🎯 What Killed the Runs", "All 30 deaths by category")

        cat_counts = data["death_messages"].groupby("category")["count_first_deaths_only"].sum().reset_index()
        cat_counts = cat_counts[cat_counts["count_first_deaths_only"] > 0]

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=cat_counts["category"],
                    values=cat_counts["count_first_deaths_only"],
                    hole=0.55,
                    marker=dict(
                        colors=[CAT_COLOR[c] for c in cat_counts["category"]],
                        line=dict(color=BG_DARK, width=4),
                    ),
                    textinfo="label+percent",
                    textfont=dict(size=14, family="monospace", color=TEXT),
                    hovertemplate="<b>%{label}</b><br>%{value} deaths<br>%{percent}<extra></extra>",
                )
            ]
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            height=420,
            annotations=[
                dict(text=f"<b>{n_failed}</b><br><span style='font-size:13px;color:{MUTED}'>deaths</span>",
                     x=0.5, y=0.5, font=dict(size=38, color=ACCENT_GOLD), showarrow=False)
            ],
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # === Time to first death (full width) ===
    section_header("⏰ How Long Each Run Lasted", "Time from world creation to first death")

    bins = [0, 5, 15, 30, 60, 120, 240, 10_000]
    labels = ["<5 min", "5–15 min", "15–30 min", "30 min – 1 h", "1–2 h", "2–4 h", "4 h+"]
    survival_binned = pd.cut(survival, bins=bins, labels=labels, right=False)
    counts = survival_binned.value_counts().reindex(labels).fillna(0).astype(int)

    median = survival.median()
    mean = survival.mean()
    longest = survival.max()
    shortest = survival.min()

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=counts.values,
                marker=dict(color=GRASS_GREEN, line=dict(color=BG_DARK, width=2)),
                text=counts.values,
                textposition="outside",
                textfont=dict(size=14, color=TEXT),
                hovertemplate="<b>%{x}</b><br>%{y} worlds<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="monospace", color=TEXT, size=13),
        height=360,
        margin=dict(l=40, r=40, t=20, b=40),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(gridcolor=BORDER, title="Worlds"),
    )
    st.plotly_chart(fig, use_container_width=True)

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Median", f"{median:.0f} min")
    sc2.metric("Mean", f"{mean:.0f} min")
    sc3.metric("Longest", f"{longest:.0f} min")
    sc4.metric("Shortest", f"{shortest:.1f} min")

    st.markdown("<br>", unsafe_allow_html=True)

    # === Fun facts ===
    longest_row = data["worlds"].sort_values("survival_minutes", ascending=False).iloc[0]
    shortest_row = data["worlds"][data["worlds"]["survival_minutes"].notna()].sort_values(
        "survival_minutes"
    ).iloc[0]

    section_header("🏆 Fun Facts")
    st.markdown(
        f"""
        <div class='fun-fact'>🏆  <b>Longest run:</b> {longest_row['survival_minutes']:.0f} minutes — ended by
        «{longest_row['first_death_player']} {longest_row['first_death_message']}» <i>(world #{int(longest_row['world_num'])})</i></div>
        <div class='fun-fact'>⚡  <b>Shortest run:</b> {shortest_row['survival_minutes']:.1f} minutes — «{shortest_row['first_death_player']} {shortest_row['first_death_message']}» <i>(world #{int(shortest_row['world_num'])})</i></div>
        <div class='fun-fact'>🌍  <b>Failure rate:</b> {100*n_failed/n_total:.0f}% of worlds ended in death</div>
        <div class='fun-fact'>⛏️  <b>Total time alive across all attempts:</b> {total_hours:.1f} hours</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # === Worlds table (expandable) ===
    with st.expander("📋 Browse every world (sortable / filterable)"):
        w = data["worlds"][[
            "world_num", "start_time", "outcome", "survival_minutes",
            "first_death_player", "first_death_message", "first_death_category",
            "total_deaths",
        ]].copy()
        w.columns = ["World #", "Started", "Outcome", "Lived (min)",
                     "First died", "Death cause", "Category", "Total deaths"]
        st.dataframe(w, use_container_width=True, hide_index=True)

    # === Footer ===
    st.markdown(f"<hr style='border-color:{BORDER};'>", unsafe_allow_html=True)
    st.caption(
        "Source: Minecraft server logs (vanilla + Forge), parsed and aggregated. "
        "Only worlds created after `hardcore=true` was enabled (2026-05-05 21:37) are counted. "
        "Cause categories: **Mob** (hostile entities), **Environment** (fall, lava, fire, etc.), **PvP** (killed by another player)."
    )


if __name__ == "__main__":
    build_app()
