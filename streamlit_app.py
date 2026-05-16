from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"

PLAYERS = ["MurzichAI", "axantroff", "trofimova2002"]

# Palette derived from in-game Minecraft block colors
PLAYER_COLOR = {
    "MurzichAI": "#DC2626",
    "axantroff": "#3DD5F3",
    "trofimova2002": "#7CB342",
}
CAT_COLOR = {
    "Mob": "#DC2626",          # redstone red
    "Environment": "#FF8C1A",  # lava orange
}
ACCENT_GOLD = "#FFAA00"
GRASS_GREEN = "#7CB342"
DIAMOND = "#3DD5F3"
BG_DARK = "#1B1D24"
SURFACE = "#2A2D36"
BORDER = "#3D4148"
TEXT = "#F5F5F5"
MUTED = "#9CA3AF"

# Emoji icons rendered native by Streamlit (no font hassles)
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
    worlds = pd.read_csv(
        DATA_DIR / "worlds.csv",
        parse_dates=["start_time", "first_death_at"],
    )
    deaths = pd.read_csv(DATA_DIR / "deaths.csv", parse_dates=["timestamp"])
    death_messages = pd.read_csv(DATA_DIR / "death_messages.csv")
    players = pd.read_csv(DATA_DIR / "players.csv")
    pvp = pd.read_csv(DATA_DIR / "pvp.csv")

    death_messages["icon"] = death_messages["death_message"].map(message_icon)
    return {
        "summary": dict(zip(summary["metric"], summary["value"])),
        "worlds": worlds,
        "deaths": deaths,
        "death_messages": death_messages,
        "players": players,
        "pvp": pvp,
    }


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
        hr {{ border-color: {BORDER} !important; }}
        .insight-card {{
            background: {SURFACE};
            border-left: 4px solid {ACCENT_GOLD};
            border-radius: 4px;
            padding: 12px 16px;
            margin: 6px 0;
            font-size: 0.95rem;
            line-height: 1.5;
        }}
        .insight-card .number {{ color: {ACCENT_GOLD}; font-weight: 800; font-size: 1.05rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    data = load_data()
    raw_worlds = data["worlds"]
    raw_deaths = data["deaths"]

    # === Title ===
    st.markdown("# ⛏️ THE HARDCORE CHRONICLES")
    st.markdown(
        f"<p style='text-align:center;color:{MUTED};font-style:italic;margin-top:-10px;'>"
        f"A Minecraft journey  —  May 5 to May 16, 2026</p>",
        unsafe_allow_html=True,
    )

    # === Filter toggle ===
    f1, f2, _ = st.columns([1.2, 1.2, 1.6])
    with f1:
        exclude_short = st.toggle(
            "Exclude worlds < 15 min active",
            value=True,
            help="Filters out worlds where total active play time was under 15 minutes — "
                 "those were almost always rerolls or messing around, not real attempts.",
        )
    with f2:
        exclude_pvp_msg = st.toggle(
            "Exclude PvP deaths",
            value=True,
            help="PvP deaths (one of us killed another) are usually goofing around, "
                 "not part of the hardcore challenge.",
        )

    # Apply filters
    worlds = raw_worlds.copy()
    if exclude_short:
        worlds = worlds[worlds["active_minutes"].fillna(0).astype(float) >= 15]
    if exclude_pvp_msg:
        worlds = worlds[~(worlds["first_death_category"].fillna("") == "PvP")]

    # Failed = died subset
    failed = worlds[worlds["outcome"] == "died"].copy()
    skipped = worlds[worlds["outcome"] == "skipped"].copy()
    active_survival = failed["active_minutes"].astype(float)

    n_total = len(worlds)
    n_failed = len(failed)
    n_skipped = len(skipped)
    total_active_hours = (
        worlds["active_minutes"].fillna(0).astype(float).sum() / 60
    )

    st.markdown(f"<hr style='border-color:{BORDER};'>", unsafe_allow_html=True)

    # === Hero metrics ===
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌍  Worlds Attempted", n_total)
    c2.metric("💀  Ended in Death", n_failed)
    c3.metric("🔄  Skipped (no death)", n_skipped)
    c4.metric("⏰  Total Active Play", f"{total_active_hours:.1f} h")

    st.markdown("<br>", unsafe_allow_html=True)

    # === Death messages bar + Category donut ===
    left, right = st.columns([2.2, 1])

    with left:
        section_header(
            "☠️ How Each Run Ended",
            "First death per world — official Minecraft death message phrasing.",
        )

        # build counts only over filtered worlds
        msg_counts = failed["first_death_message"].value_counts().reset_index()
        msg_counts.columns = ["death_message", "count"]
        msg_counts = msg_counts.merge(
            data["death_messages"][["death_message", "category", "icon"]],
            on="death_message", how="left",
        )
        msg_counts["label"] = msg_counts.apply(
            lambda r: f"{r['icon']}  <player> {r['death_message']}", axis=1
        )
        # Global desc ordering by count, regardless of category color groupings.
        msg_counts = msg_counts.sort_values("count", ascending=True)

        if msg_counts.empty:
            st.info("No deaths after filters applied.")
        else:
            color_map = {**CAT_COLOR, "PvP": MUTED, "Other": MUTED}
            fig = px.bar(
                msg_counts, x="count", y="label", orientation="h",
                color="category", color_discrete_map=color_map,
                text="count",
                labels={"count": "Worlds ended this way", "label": ""},
                height=max(360, 40 * len(msg_counts) + 100),
            )
            fig.update_traces(
                textposition="outside",
                textfont=dict(size=14, color=TEXT),
                marker_line_color=BG_DARK,
                marker_line_width=2,
            )
            # Force a global sort across categories — without this, plotly
            # creates one trace per color and groups bars by category.
            fig.update_yaxes(
                categoryorder="array",
                categoryarray=msg_counts["label"].tolist(),
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="monospace", color=TEXT, size=13),
                margin=dict(l=10, r=40, t=10, b=40),
                xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
                yaxis=dict(gridcolor="rgba(0,0,0,0)"),
                legend=dict(
                    title="Cause", orientation="h", yanchor="bottom", y=-0.18,
                    xanchor="right", x=1, bgcolor=SURFACE,
                    bordercolor=BORDER, borderwidth=1, font=dict(color=TEXT),
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

    with right:
        section_header("🎯 Mob vs Environment", "Of all hardcore-ending deaths.")

        # Only show Mob and Environment, exclude PvP/Other from donut
        cat = failed["first_death_category"].copy()
        cat_counts = cat[cat.isin(["Mob", "Environment"])].value_counts().reset_index()
        cat_counts.columns = ["category", "n"]

        if cat_counts.empty:
            st.info("No categorized deaths after filters.")
        else:
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=cat_counts["category"],
                        values=cat_counts["n"],
                        hole=0.6,
                        marker=dict(
                            colors=[CAT_COLOR[c] for c in cat_counts["category"]],
                            line=dict(color=BG_DARK, width=4),
                        ),
                        textinfo="label+percent",
                        textfont=dict(size=15, family="monospace", color=TEXT),
                        hovertemplate="<b>%{label}</b><br>%{value} deaths<br>%{percent}<extra></extra>",
                    )
                ]
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                height=420,
                annotations=[
                    dict(
                        text=f"<b>{cat_counts['n'].sum()}</b><br>"
                             f"<span style='font-size:13px;color:{MUTED}'>deaths</span>",
                        x=0.5, y=0.5, font=dict(size=38, color=ACCENT_GOLD), showarrow=False,
                    )
                ],
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # === Time-to-first-death histogram (using ACTIVE minutes) ===
    section_header(
        "⏰ How Long Each Run Lasted",
        "Active play time from world creation to first death — idle / overnight server time is excluded.",
    )

    if active_survival.empty:
        st.info("No deaths after filters applied.")
    else:
        bins = [0, 5, 15, 30, 60, 120, 240, 10_000]
        labels = ["<5 min", "5–15 min", "15–30 min", "30 min – 1 h", "1–2 h", "2–4 h", "4 h+"]
        survival_binned = pd.cut(active_survival, bins=bins, labels=labels, right=False)
        counts = survival_binned.value_counts().reindex(labels).fillna(0).astype(int)

        fig = go.Figure(
            data=[
                go.Bar(
                    x=labels, y=counts.values,
                    marker=dict(color=GRASS_GREEN, line=dict(color=BG_DARK, width=2)),
                    text=counts.values, textposition="outside",
                    textfont=dict(size=14, color=TEXT),
                    hovertemplate="<b>%{x}</b><br>%{y} worlds<extra></extra>",
                )
            ]
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="monospace", color=TEXT, size=13),
            height=360,
            margin=dict(l=40, r=40, t=20, b=40),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
            yaxis=dict(gridcolor=BORDER, title="Worlds"),
        )
        st.plotly_chart(fig, use_container_width=True)

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Median", f"{active_survival.median():.0f} min")
        sc2.metric("Mean",   f"{active_survival.mean():.0f} min")
        sc3.metric("Longest", f"{active_survival.max():.0f} min")
        sc4.metric("Shortest", f"{active_survival.min():.1f} min")

    st.markdown("<br>", unsafe_allow_html=True)

    # === Per-player tally ===
    section_header(
        "👥 Per Player",
        "First deaths (run-ending) and total deaths each player accumulated across the filtered worlds.",
    )

    if failed.empty:
        st.info("No deaths after filters applied.")
    else:
        first_by = (
            failed["first_death_player"].value_counts()
            .reindex(PLAYERS).fillna(0).astype(int)
        )
        deaths_filtered = raw_deaths[raw_deaths["world_num"].isin(worlds["world_num"])]
        total_by = (
            deaths_filtered["player"].value_counts()
            .reindex(PLAYERS).fillna(0).astype(int)
        )

        pp_df = pd.DataFrame({
            "player": PLAYERS,
            "First deaths": [int(first_by[p]) for p in PLAYERS],
            "Total deaths": [int(total_by[p]) for p in PLAYERS],
        }).sort_values("First deaths", ascending=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=pp_df["First deaths"], y=pp_df["player"], orientation="h",
            name="First deaths (run-ending)",
            marker=dict(
                color=[PLAYER_COLOR[p] for p in pp_df["player"]],
                line=dict(color=BG_DARK, width=2),
            ),
            text=pp_df["First deaths"], textposition="outside",
            textfont=dict(size=14, color=TEXT),
            hovertemplate="<b>%{y}</b><br>First deaths: %{x}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            x=pp_df["Total deaths"], y=pp_df["player"], orientation="h",
            name="Total deaths (incl. post-first)",
            marker=dict(
                color=[PLAYER_COLOR[p] for p in pp_df["player"]],
                opacity=0.35,
                line=dict(color=BG_DARK, width=2),
            ),
            text=pp_df["Total deaths"], textposition="outside",
            textfont=dict(size=14, color=MUTED),
            hovertemplate="<b>%{y}</b><br>Total deaths: %{x}<extra></extra>",
            visible="legendonly",
        ))
        fig.update_layout(
            barmode="overlay",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="monospace", color=TEXT, size=14),
            margin=dict(l=10, r=40, t=10, b=40),
            xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, title="Worlds"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=14)),
            height=280,
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.35, xanchor="right", x=1,
                bgcolor=SURFACE, bordercolor=BORDER, borderwidth=1, font=dict(color=TEXT),
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

        cols = st.columns(len(PLAYERS))
        for col, p in zip(cols, PLAYERS):
            with col:
                st.markdown(
                    f"""
                    <div style='background:{SURFACE};border:2px solid {PLAYER_COLOR[p]};
                                border-radius:6px;padding:14px 18px;text-align:center;'>
                        <div style='color:{PLAYER_COLOR[p]};font-weight:800;font-size:1.05rem;
                                    letter-spacing:0.03em;'>{p}</div>
                        <div style='color:{TEXT};font-size:0.85rem;margin-top:8px;'>
                            <b style='color:{ACCENT_GOLD};'>{int(first_by[p])}</b> first deaths
                            &nbsp;·&nbsp;
                            <b style='color:{ACCENT_GOLD};'>{int(total_by[p])}</b> total
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)

    # === Key insights (unique stats, not duplicated above) ===
    section_header("💡 Key Insights")
    if not failed.empty:
        msg_cnt = failed["first_death_message"].value_counts()
        top1_msg, top1_n = msg_cnt.index[0], msg_cnt.iloc[0]
        top3_share = 100 * msg_cnt.head(3).sum() / msg_cnt.sum()
        unique_msgs = len(msg_cnt)
        only_once = msg_cnt[msg_cnt == 1]
        cat_share = failed["first_death_category"].value_counts(normalize=True) * 100

        # Specific killer extraction (e.g., "by Creeper" -> Creeper)
        import re as _re
        killer_re = _re.compile(r"by ([A-Z][\w-]+(?: [A-Z][\w-]+)?)")
        specific_killer = failed["first_death_message"].apply(
            lambda m: (killer_re.search(m).group(1) if killer_re.search(m) else None)
        )
        sk_counts = specific_killer.dropna().value_counts()

        insights = []
        insights.append(
            f"💥 <span class='number'>{100*top1_n/msg_cnt.sum():.0f}%</span> of failed runs "
            f"ended with «{top1_msg}» ({top1_n} of {msg_cnt.sum()})"
        )
        insights.append(
            f"📊 Top 3 death causes account for "
            f"<span class='number'>{top3_share:.0f}%</span> of all failed runs"
        )
        insights.append(
            f"🔢 <span class='number'>{unique_msgs}</span> different death messages "
            f"happened — <span class='number'>{len(only_once)}</span> only once "
            f"({', '.join(only_once.index[:3].tolist())}{'…' if len(only_once)>3 else ''})"
        )
        if "Mob" in cat_share:
            insights.append(
                f"🧟 Hostile mobs caused "
                f"<span class='number'>{cat_share['Mob']:.0f}%</span> of all hardcore endings; "
                f"environment caused <span class='number'>"
                f"{cat_share.get('Environment',0):.0f}%</span>"
            )
        if not sk_counts.empty:
            insights.append(
                f"🏆 Deadliest specific enemy: <span class='number'>{sk_counts.index[0]}</span> "
                f"({sk_counts.iloc[0]} kills)"
            )
        # Average active time before death
        insights.append(
            f"⏱  An average run lasted "
            f"<span class='number'>{active_survival.mean():.0f} active minutes</span> "
            f"before someone died"
        )

        for ins in insights:
            st.markdown(f"<div class='insight-card'>{ins}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # === Browse worlds (uses filtered list) ===
    with st.expander(f"📋 Browse every world  ({n_total} after filters)"):
        w = worlds.copy()
        w["outcome"] = w["outcome"].map({"died": "Died", "skipped": "Skipped (no death)"})
        w = w[[
            "world_num", "start_time", "outcome", "active_minutes", "wallclock_minutes",
            "first_death_player", "first_death_message", "first_death_category", "total_deaths",
        ]]
        w.columns = [
            "World #", "Started", "Outcome", "Active (min)", "Wall-clock (min)",
            "First died", "Death cause", "Category", "Total deaths",
        ]
        st.dataframe(w, use_container_width=True, hide_index=True)

    # === Footer ===
    st.markdown(f"<hr style='border-color:{BORDER};'>", unsafe_allow_html=True)
    st.caption(
        f"Source: Minecraft server logs (vanilla + Forge). Only worlds created after "
        f"`hardcore=true` was enabled (2026-05-05 21:37). "
        f"Active minutes = wall-clock time where at least one player was logged in "
        f"(computed from `joined the game` / `left the game` events). "
        f"Filters above apply to all charts."
    )


if __name__ == "__main__":
    build_app()
