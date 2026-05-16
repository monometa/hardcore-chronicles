from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from i18n import (
    advancement_label,
    cause_label,
    death_message_label,
    language_selector,
    outcome_label,
    ru_verb,
    tr,
    unit_hours,
    unit_minutes,
)

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
    worlds = pd.read_csv(DATA_DIR / "worlds.csv")
    worlds["start_time"] = pd.to_datetime(worlds["start_time"], format="ISO8601")
    worlds["first_death_at"] = pd.to_datetime(
        worlds["first_death_at"], format="ISO8601"
    )
    deaths = pd.read_csv(DATA_DIR / "deaths.csv")
    deaths["timestamp"] = pd.to_datetime(deaths["timestamp"], format="ISO8601")
    death_messages = pd.read_csv(DATA_DIR / "death_messages.csv")
    players = pd.read_csv(DATA_DIR / "players.csv")
    pvp = pd.read_csv(DATA_DIR / "pvp.csv")
    advancements = pd.read_csv(DATA_DIR / "advancements.csv")
    advancements["timestamp"] = pd.to_datetime(
        advancements["timestamp"], format="ISO8601"
    )

    death_messages["icon"] = death_messages["death_message"].map(message_icon)
    return {
        "summary": dict(zip(summary["metric"], summary["value"])),
        "worlds": worlds,
        "deaths": deaths,
        "death_messages": death_messages,
        "players": players,
        "pvp": pvp,
        "advancements": advancements,
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

    lang = language_selector()
    died_label = outcome_label("died", lang, compact=True)
    rerolled_label = outcome_label("skipped", lang, compact=True)

    data = load_data()
    raw_worlds = data["worlds"]
    raw_deaths = data["deaths"]

    # === Title ===
    st.markdown("# ⛏️ THE HARDCORE CHRONICLES")
    st.markdown(
        f"<p style='text-align:center;color:{MUTED};font-style:italic;margin-top:-10px;'>"
        f"{tr(lang, 'A Minecraft journey', 'Наш Minecraft-марафон')}  —  "
        f"{tr(lang, 'May 5 to May 16, 2026', '5-16 мая 2026')}</p>",
        unsafe_allow_html=True,
    )

    # === Filter toggle ===
    # PvP-categorized deaths are always excluded — those happened during goofing
    # around between friends, not real hardcore attempts. The toggle was dropped
    # because it only affected ~1 in 10 worlds and clogged the top of the page.
    f1, _ = st.columns([1.2, 2.8])
    with f1:
        exclude_short = st.toggle(
            tr(lang, "Exclude worlds < 15 min active", "Скрыть миры < 15 мин активной игры"),
            value=False,
            help=tr(
                lang,
                "Filters out worlds where total active play time was under 15 minutes — "
                "those were almost always rerolls or messing around, not real attempts.",
                "Убирает миры, где активной игры было меньше 15 минут. "
                "Это почти всегда быстрые рероллы или возня между попытками.",
            ),
        )

    # Apply filters — drive every chart/insight on the page, including the hero.
    worlds = raw_worlds.copy()
    worlds = worlds[~(worlds["first_death_category"].fillna("") == "PvP")]
    if exclude_short:
        worlds = worlds[worlds["active_minutes"].fillna(0).astype(float) >= 15]

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

    # === Hero metrics (respect the toggle above) ===
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(tr(lang, "🌍  Worlds Attempted", "🌍  Миров создано"), n_total)
    c2.metric(tr(lang, "💀  Ended in Death", "💀  Закончились смертью"), n_failed)
    c3.metric(tr(lang, "🔄  Skipped (no death)", "🔄  Рероллы без смерти"), n_skipped)
    c4.metric(
        tr(lang, "⏰  Total Active Play", "⏰  Активной игры"),
        f"{total_active_hours:.1f} {unit_hours(lang)}",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # === Worlds per Day ===
    section_header(
        tr(lang, "📅 Worlds Per Day", "📅 Миры по дням"),
        tr(
            lang,
            "Daily attempt count. Outcome stacked: red = ended in death, gold = rerolled.",
            "Сколько попыток начиналось каждый день. Красное = смерть, золото = реролл.",
        ),
    )

    if worlds.empty:
        st.info(tr(lang, "No worlds after filters applied.", "После фильтров не осталось миров."))
    else:
        per_day = worlds.copy()
        per_day["day"] = per_day["start_time"].dt.date
        per_day["outcome_label"] = per_day["outcome"].map(
            {"died": died_label, "skipped": rerolled_label}
        )
        grouped = (
            per_day.groupby(["day", "outcome_label"])
            .size().reset_index(name="count")
        )
        # Reindex onto a contiguous daily range so empty days appear as gaps.
        all_days = pd.date_range(per_day["day"].min(), per_day["day"].max(), freq="D").date
        fig = px.bar(
            grouped, x="day", y="count", color="outcome_label",
            color_discrete_map={died_label: "#DC2626", rerolled_label: ACCENT_GOLD},
            text="count",
            labels={
                "day": "",
                "count": tr(lang, "Worlds", "Миры"),
                "outcome_label": tr(lang, "Outcome", "Итог"),
            },
            category_orders={"outcome_label": [died_label, rerolled_label]},
            height=300,
        )
        fig.update_traces(
            textposition="inside", insidetextanchor="middle",
            textfont=dict(size=12, color=BG_DARK),
            marker_line_color=BG_DARK, marker_line_width=2,
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="monospace", color=TEXT, size=13),
            margin=dict(l=40, r=40, t=10, b=40),
            barmode="stack",
            xaxis=dict(
                gridcolor="rgba(0,0,0,0)",
                tickmode="array",
                tickvals=list(all_days),
                tickformat="%b %-d",
                tickangle=-45,
            ),
            yaxis=dict(gridcolor=BORDER, title=tr(lang, "Worlds started", "Миров начато")),
            legend=dict(
                orientation="h", yanchor="bottom", y=-0.35, xanchor="right", x=1,
                bgcolor=SURFACE, bordercolor=BORDER, borderwidth=1, font=dict(color=TEXT),
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Quick numerical context below the chart.
        days_played = per_day["day"].nunique()
        worlds_per_day = n_total / days_played if days_played else 0
        peak_day_count = grouped.groupby("day")["count"].sum().max()
        peak_day = (
            grouped.groupby("day")["count"].sum()
            .sort_values(ascending=False).index[0]
        )
        pd1, pd2, pd3 = st.columns(3)
        pd1.metric(tr(lang, "Days Played", "Дней игры"), f"{days_played}")
        pd2.metric(tr(lang, "Avg Worlds / Day", "Миров в день"), f"{worlds_per_day:.1f}")
        pd3.metric(
            tr(lang, "Peak Day", "Самый плотный день"),
            tr(lang, f"{peak_day_count} worlds", f"{peak_day_count} миров"),
            help=tr(lang, f"On {peak_day.strftime('%b %-d')}", f"{peak_day.strftime('%d.%m.%Y')}"),
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # === Death messages bar + Category donut ===
    left, right = st.columns([2.2, 1])

    with left:
        section_header(
            tr(lang, "☠️ How Each Run Ended", "☠️ Чем заканчивались попытки"),
            tr(
                lang,
                "First death per world.",
                "Первая смерть в каждом мире.",
            ),
        )

        # build counts only over filtered worlds
        msg_counts = failed["first_death_message"].value_counts().reset_index()
        msg_counts.columns = ["death_message", "count"]
        msg_counts = msg_counts.merge(
            data["death_messages"][["death_message", "category", "icon"]],
            on="death_message", how="left",
        )
        msg_counts["category_label"] = msg_counts["category"].map(lambda c: cause_label(c, lang))
        msg_counts["label"] = msg_counts.apply(
            lambda r: f"{r['icon']}  <player> {death_message_label(r['death_message'], lang)}",
            axis=1,
        )
        # Global desc ordering by count, regardless of category color groupings.
        msg_counts = msg_counts.sort_values("count", ascending=True)

        if msg_counts.empty:
            st.info(tr(lang, "No deaths after filters applied.", "После фильтров не осталось смертей."))
        else:
            color_map = {
                cause_label(k, lang): v for k, v in {**CAT_COLOR, "PvP": MUTED, "Other": MUTED}.items()
            }
            fig = px.bar(
                msg_counts, x="count", y="label", orientation="h",
                color="category_label", color_discrete_map=color_map,
                text="count",
                labels={
                    "count": tr(lang, "Worlds ended this way", "Миров закончилось так"),
                    "label": "",
                    "category_label": tr(lang, "Cause", "Причина"),
                },
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
                    title=tr(lang, "Cause", "Причина"), orientation="h", yanchor="bottom", y=-0.18,
                    xanchor="right", x=1, bgcolor=SURFACE,
                    bordercolor=BORDER, borderwidth=1, font=dict(color=TEXT),
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

    with right:
        section_header(
            tr(lang, "🎯 Mob vs Environment", "🎯 Мобы против среды"),
            tr(lang, "Of all hardcore-ending deaths.", "Среди всех смертей, которые закрыли попытку."),
        )

        # Only show Mob and Environment, exclude PvP/Other from donut
        cat = failed["first_death_category"].copy()
        cat_counts = cat[cat.isin(["Mob", "Environment"])].value_counts().reset_index()
        cat_counts.columns = ["category", "n"]
        cat_counts["category_label"] = cat_counts["category"].map(lambda c: cause_label(c, lang))

        if cat_counts.empty:
            st.info(tr(lang, "No categorized deaths after filters.", "После фильтров нет смертей с категорией."))
        else:
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=cat_counts["category_label"],
                        values=cat_counts["n"],
                        hole=0.6,
                        marker=dict(
                            colors=[CAT_COLOR[c] for c in cat_counts["category"]],
                            line=dict(color=BG_DARK, width=4),
                        ),
                        textinfo="label+percent",
                        textfont=dict(size=15, family="monospace", color=TEXT),
                        hovertemplate=tr(
                            lang,
                            "<b>%{label}</b><br>%{value} deaths<br>%{percent}<extra></extra>",
                            "<b>%{label}</b><br>%{value} смертей<br>%{percent}<extra></extra>",
                        ),
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
                             f"<span style='font-size:13px;color:{MUTED}'>"
                             f"{tr(lang, 'deaths', 'смертей')}</span>",
                        x=0.5, y=0.5, font=dict(size=38, color=ACCENT_GOLD), showarrow=False,
                    )
                ],
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # === Time-to-first-death histogram (using ACTIVE minutes) ===
    section_header(
        tr(lang, "⏰ How Long Each Run Lasted", "⏰ Сколько жили попытки"),
        tr(
            lang,
            "Active play time from world creation to first death.",
            "Активное время от создания мира до первой смерти.",
        ),
    )

    if active_survival.empty:
        st.info(tr(lang, "No deaths after filters applied.", "После фильтров не осталось смертей."))
    else:
        bins = [0, 5, 15, 30, 60, 120, 240, 10_000]
        labels = tr(
            lang,
            ["<5 min", "5–15 min", "15–30 min", "30 min – 1 h", "1–2 h", "2–4 h", "4 h+"],
            ["<5 мин", "5-15 мин", "15-30 мин", "30 мин - 1 ч", "1-2 ч", "2-4 ч", "4 ч+"],
        )
        survival_binned = pd.cut(active_survival, bins=bins, labels=labels, right=False)
        counts = survival_binned.value_counts().reindex(labels).fillna(0).astype(int)

        fig = go.Figure(
            data=[
                go.Bar(
                    x=labels, y=counts.values,
                    marker=dict(color=GRASS_GREEN, line=dict(color=BG_DARK, width=2)),
                    text=counts.values, textposition="outside",
                    textfont=dict(size=14, color=TEXT),
                    hovertemplate=tr(
                        lang,
                        "<b>%{x}</b><br>%{y} worlds<extra></extra>",
                        "<b>%{x}</b><br>%{y} миров<extra></extra>",
                    ),
                )
            ]
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="monospace", color=TEXT, size=13),
            height=360,
            margin=dict(l=40, r=40, t=20, b=40),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
            yaxis=dict(gridcolor=BORDER, title=tr(lang, "Worlds", "Миры")),
        )
        st.plotly_chart(fig, use_container_width=True)

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric(tr(lang, "Median", "Медиана"), f"{active_survival.median():.0f} {unit_minutes(lang)}")
        sc2.metric(tr(lang, "Mean", "Среднее"), f"{active_survival.mean():.0f} {unit_minutes(lang)}")
        sc3.metric(tr(lang, "Longest", "Самая долгая"), f"{active_survival.max():.0f} {unit_minutes(lang)}")
        sc4.metric(tr(lang, "Shortest", "Самая короткая"), f"{active_survival.min():.1f} {unit_minutes(lang)}")

    st.markdown("<br>", unsafe_allow_html=True)

    # === Achievements / Progression ===
    section_header(
        tr(lang, "🏆 How Far Each Run Got", "🏆 До чего мы доходили"),
        "",
    )

    adv = data["advancements"]
    adv_filt = adv[adv["world_num"].isin(worlds["world_num"])]
    n_filt_worlds = len(worlds)

    if adv_filt.empty:
        st.info(tr(lang, "No advancements after filters applied.", "После фильтров не осталось достижений."))
    else:
        # --- Hero stats row ---
        unique_advs = adv_filt["advancement"].nunique()
        total_adv_events = len(adv_filt)
        worlds_with_iron = adv_filt[adv_filt["advancement"] == "Acquire Hardware"][
            "world_num"
        ].nunique()
        worlds_with_diamond = adv_filt[adv_filt["advancement"] == "Diamonds!"][
            "world_num"
        ].nunique()
        worlds_with_nether = adv_filt[
            adv_filt["advancement"] == "We Need to Go Deeper"
        ]["world_num"].nunique()

        a1, a2, a3, a4 = st.columns(4)
        a1.metric(
            tr(lang, "🏅  Unique Advancements", "🏅  Уникальных достижений"),
            f"{unique_advs}",
            help=tr(
                lang,
                f"{total_adv_events} broadcasts in total across these worlds.",
                f"{total_adv_events} сообщений о достижениях в этих мирах.",
            ),
        )
        a2.metric(
            tr(lang, "⛏️  Worlds Reached Iron", "⛏️  Миры дошли до железа"),
            f"{worlds_with_iron} / {n_filt_worlds}",
            help=tr(
                lang,
                "Worlds where any player got the 'Acquire Hardware' advancement.",
                "Миры, где кто-то получил достижение 'Куй железо...'.",
            ),
        )
        a3.metric(
            tr(lang, "💎  Worlds Reached Diamond", "💎  Миры дошли до алмазов"),
            f"{worlds_with_diamond} / {n_filt_worlds}",
            help=tr(
                lang,
                "Worlds where any player got the 'Diamonds!' advancement.",
                "Миры, где кто-то получил достижение 'Алмазы!'.",
            ),
        )
        a4.metric(
            tr(lang, "🔥  Worlds Reached Nether", "🔥  Миры дошли до Незера"),
            f"{worlds_with_nether} / {n_filt_worlds}",
            help=tr(
                lang,
                "Worlds where any player got 'We Need to Go Deeper'.",
                "Миры, где кто-то получил достижение 'Огненные недра'.",
            ),
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Progression funnel: how many worlds reached each milestone ---
        # Milestones ordered by natural progression. Reach = unique worlds where
        # any player triggered the advancement.
        milestone_order = [
            ("Stone Age",            "🪨", tr(lang, "first cobblestone", "первый булыжник")),
            ("Sweet Dreams",         "🛏️", tr(lang, "first sleep", "первый сон")),
            ("Suit Up",              "🛡️", tr(lang, "first armor", "первая броня")),
            ("Getting an Upgrade",   "🔨", tr(lang, "first stone tool", "первый каменный инструмент")),
            ("Acquire Hardware",     "⛏️", tr(lang, "first iron ingot", "первый железный слиток")),
            ("Isn't It Iron Pick",   "⚒️", tr(lang, "first iron pick", "первая железная кирка")),
            ("Hot Stuff",            "🪣", tr(lang, "first lava bucket", "первое ведро лавы")),
            ("Ice Bucket Challenge", "🧊", tr(lang, "first obsidian", "первый обсидиан")),
            ("Diamonds!",            "💎", tr(lang, "first diamond", "первый алмаз")),
            ("Cover Me with Diamonds","🛡️", tr(lang, "diamond armor", "алмазная броня")),
            ("We Need to Go Deeper", "🌋", tr(lang, "entered the Nether", "вошли в Незер")),
            ("A Terrible Fortress",  "🏰", tr(lang, "found Nether fortress", "нашли крепость Незера")),
            ("Into Fire",            "🔥", tr(lang, "got blaze rod", "добыли огненный стержень")),
            ("Eye Spy",              "👁️", tr(lang, "got ender eye", "получили око Эндера")),
            ("The End?",             "🐉", tr(lang, "reached The End", "дошли до Края")),
        ]
        reach = []
        for adv_name, icon, blurb in milestone_order:
            n = adv_filt[adv_filt["advancement"] == adv_name]["world_num"].nunique()
            if n == 0:
                continue
            reach.append(
                {
                    "label": f"{icon}  {adv_name}",
                    "display_label": f"{icon}  {advancement_label(adv_name, lang)}",
                    "blurb": blurb,
                    "n_worlds": n,
                    "pct": 100 * n / n_filt_worlds,
                }
            )
        reach_df = pd.DataFrame(reach)
        # Plot top-down: the deepest milestone reached at top? No — natural reading
        # is "broad at top, narrows down". So highest reach first.
        reach_df = reach_df.sort_values("n_worlds", ascending=True)

        funnel = go.Figure(
            data=[
                go.Bar(
                    x=reach_df["n_worlds"], y=reach_df["display_label"], orientation="h",
                    marker=dict(
                        color=reach_df["n_worlds"],
                        colorscale=[
                            [0.0, "#3D4148"], [0.5, "#FF8C1A"], [1.0, ACCENT_GOLD],
                        ],
                        showscale=False,
                        line=dict(color=BG_DARK, width=2),
                    ),
                    text=reach_df.apply(
                        lambda r: f"{r['n_worlds']} ({r['pct']:.0f}%)", axis=1
                    ),
                    textposition="outside",
                    textfont=dict(size=13, color=TEXT),
                    customdata=reach_df["blurb"],
                    hovertemplate=(
                        "<b>%{y}</b><br>%{customdata}<br>"
                        + tr(lang, "%{x} worlds reached this", "%{x} миров дошли сюда")
                        + "<extra></extra>"
                    ),
                )
            ]
        )
        funnel.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="monospace", color=TEXT, size=13),
            height=max(360, 36 * len(reach_df) + 80),
            margin=dict(l=10, r=80, t=10, b=40),
            xaxis=dict(
                gridcolor=BORDER, zerolinecolor=BORDER,
                title=tr(
                    lang,
                    f"Worlds reaching this milestone (out of {n_filt_worlds})",
                    f"Миров с этим достижением (из {n_filt_worlds})",
                ),
                range=[0, max(reach_df["n_worlds"]) * 1.18],
            ),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(funnel, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Time-to-milestone strip + per-player advancement counts ---
        # (Named `leader_col` historically; not a leaderboard per task.md §4 #2.)
        ttm_col, leader_col = st.columns([1.3, 1])

        with ttm_col:
            section_header(
                tr(lang, "⚡ Fastest Progression", "⚡ Самый быстрый прогресс"),
                tr(
                    lang,
                    "Median / fastest time from world start to first time anyone "
                    "in the group earned this advancement.",
                    "Медиана и рекорд от старта мира до первого получения достижения кем-то из группы.",
                ),
            )
            milestones_for_ttm = [
                ("Stone Age", "🪨"),
                ("Sweet Dreams", "🛏️"),
                ("Acquire Hardware", "⛏️"),
                ("Diamonds!", "💎"),
                ("We Need to Go Deeper", "🌋"),
                ("A Terrible Fortress", "🏰"),
            ]
            ttm_rows = []
            for adv_name, icon in milestones_for_ttm:
                sub = adv_filt[adv_filt["advancement"] == adv_name]
                if sub.empty:
                    continue
                # First time per world (across any player).
                first_per_world = (
                    sub.groupby("world_num")["minutes_into_run"]
                    .min().astype(float)
                )
                ttm_rows.append({
                    tr(lang, "Milestone", "Этап"): f"{icon}  {advancement_label(adv_name, lang)}",
                    tr(lang, "Worlds", "Миры"): len(first_per_world),
                    tr(lang, "Fastest", "Рекорд"): f"{first_per_world.min():.0f} {unit_minutes(lang)}",
                    tr(lang, "Median", "Медиана"): f"{first_per_world.median():.0f} {unit_minutes(lang)}",
                })
            ttm_df = pd.DataFrame(ttm_rows)
            st.dataframe(ttm_df, use_container_width=True, hide_index=True)

        with leader_col:
            section_header(
                tr(lang, "👤 Unique Per Player", "👤 Уникальных на игрока"),
                tr(
                    lang,
                    "Unique advancements each player has personally earned.",
                    "Сколько разных достижений каждый игрок получил лично.",
                ),
            )
            per_player = (
                adv_filt.groupby("player")["advancement"]
                .nunique().reindex(PLAYERS).fillna(0).astype(int)
                .sort_values(ascending=True)
            )
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=per_player.values, y=per_player.index, orientation="h",
                        marker=dict(
                            color=[PLAYER_COLOR[p] for p in per_player.index],
                            line=dict(color=BG_DARK, width=2),
                        ),
                        text=per_player.values, textposition="outside",
                        textfont=dict(size=14, color=TEXT),
                        hovertemplate=tr(
                            lang,
                            "<b>%{y}</b><br>%{x} unique advancements<extra></extra>",
                            "<b>%{y}</b><br>%{x} уникальных достижений<extra></extra>",
                        ),
                    )
                ]
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="monospace", color=TEXT, size=14),
                margin=dict(l=10, r=40, t=10, b=20), height=220,
                xaxis=dict(
                    gridcolor=BORDER, zerolinecolor=BORDER,
                    range=[0, per_player.max() * 1.25 if per_player.max() else 1],
                ),
                yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Rare achievements + Last-before-death narrative ---
        section_header(tr(lang, "🌟 Highlights", "🌟 Самые обидные и редкие моменты"))

        # Singletons: advancements earned in only ONE world ever.
        worlds_per_adv = (
            adv_filt.groupby("advancement")["world_num"].nunique()
            .sort_values()
        )
        singletons = worlds_per_adv[worlds_per_adv == 1].index.tolist()

        # Last advancement earned before first-death in each world.
        last_before = []
        for _, w_row in worlds.iterrows():
            wn = w_row["world_num"]
            dt = w_row["first_death_at"]
            if pd.isna(dt):
                continue
            advs_in_world = adv_filt[adv_filt["world_num"] == wn].sort_values("timestamp")
            before = advs_in_world[advs_in_world["timestamp"] < dt]
            if before.empty:
                continue
            last_row = before.iloc[-1]
            gap_min = (dt - last_row["timestamp"]).total_seconds() / 60
            last_before.append(
                {
                    "world_num": wn,
                    "player": last_row["player"],
                    "advancement": last_row["advancement"],
                    "gap_min": gap_min,
                    "death_player": w_row["first_death_player"],
                    "death_msg": w_row["first_death_message"],
                }
            )
        last_before.sort(key=lambda r: r["gap_min"])

        highlight_cards = []
        if singletons:
            highlight_cards.append(
                tr(lang, "💫 Only-once unlocks: ", "💫 Достижения, которые случились только один раз: ")
                + ", ".join(f"<b>{advancement_label(s, lang)}</b>" for s in singletons[:6])
                + (
                    tr(lang, f" and {len(singletons)-6} more", f" и ещё {len(singletons)-6}")
                    if len(singletons) > 6 else ""
                )
            )

        # Worlds that reached The End vs total — the meta narrative.
        end_count = adv_filt[adv_filt["advancement"] == "The End?"]["world_num"].nunique()
        if end_count > 0:
            highlight_cards.append(
                tr(
                    lang,
                    f"🐉 We reached <span class='number'>The End</span> in "
                    f"<span class='number'>{end_count}</span> world(s) "
                    f"— and died before killing the dragon every time.",
                    f"🐉 Мы дошли до <span class='number'>Края</span> в "
                    f"<span class='number'>{end_count}</span> мире "
                    f"и всё равно умерли до убийства дракона.",
                )
            )

        # Ironic last-before-death examples: shortest gap between advancement and death.
        if last_before:
            top = last_before[0]
            highlight_cards.append(
                tr(
                    lang,
                    f"⏱  Cruelest gap: <b>{top['death_player']}</b> died "
                    f"<span class='number'>{top['gap_min']:.1f} min</span> after "
                    f"<b>{top['player']}</b> unlocked "
                    f"<b>{top['advancement']}</b> (world #{top['world_num']}).",
                    f"⏱  Самый жестокий зазор: <b>{top['death_player']}</b> "
                    f"{ru_verb(top['death_player'], 'умер', 'умерла')} через "
                    f"<span class='number'>{top['gap_min']:.1f} мин</span> после того, как "
                    f"<b>{top['player']}</b> "
                    f"{ru_verb(top['player'], 'получил', 'получила')} "
                    f"<b>{advancement_label(top['advancement'], lang)}</b> (мир #{top['world_num']}).",
                )
            )

        # Most-reached vs least-reached among those we DID achieve.
        if not worlds_per_adv.empty:
            top_adv = worlds_per_adv.idxmax()
            top_n = worlds_per_adv.max()
            highlight_cards.append(
                tr(
                    lang,
                    f"🏆 Most-frequent unlock: <b>{top_adv}</b> earned in "
                    f"<span class='number'>{top_n}</span> different worlds "
                    f"({100*top_n/n_filt_worlds:.0f}% of attempts).",
                    f"🏆 Самое частое достижение: <b>{advancement_label(top_adv, lang)}</b> "
                    f"в <span class='number'>{top_n}</span> разных мирах "
                    f"({100*top_n/n_filt_worlds:.0f}% попыток).",
                )
            )

        for ins in highlight_cards:
            st.markdown(f"<div class='insight-card'>{ins}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # === Per-player tally ===
    section_header(
        tr(lang, "👥 Per Player", "👥 По игрокам"),
        tr(
            lang,
            "First deaths (run-ending) and total deaths each player accumulated across the filtered worlds.",
            "Первые смерти, которые закрывали мир, и все смерти каждого игрока в отфильтрованных мирах.",
        ),
    )

    if failed.empty:
        st.info(tr(lang, "No deaths after filters applied.", "После фильтров не осталось смертей."))
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
            "first_deaths": [int(first_by[p]) for p in PLAYERS],
            "total_deaths": [int(total_by[p]) for p in PLAYERS],
        }).sort_values("first_deaths", ascending=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=pp_df["first_deaths"], y=pp_df["player"], orientation="h",
            name=tr(lang, "First deaths (run-ending)", "Первые смерти"),
            marker=dict(
                color=[PLAYER_COLOR[p] for p in pp_df["player"]],
                line=dict(color=BG_DARK, width=2),
            ),
            text=pp_df["first_deaths"], textposition="outside",
            textfont=dict(size=14, color=TEXT),
            hovertemplate=tr(
                lang,
                "<b>%{y}</b><br>First deaths: %{x}<extra></extra>",
                "<b>%{y}</b><br>Первые смерти: %{x}<extra></extra>",
            ),
        ))
        fig.add_trace(go.Bar(
            x=pp_df["total_deaths"], y=pp_df["player"], orientation="h",
            name=tr(lang, "Total deaths (incl. post-first)", "Все смерти"),
            marker=dict(
                color=[PLAYER_COLOR[p] for p in pp_df["player"]],
                opacity=0.35,
                line=dict(color=BG_DARK, width=2),
            ),
            text=pp_df["total_deaths"], textposition="outside",
            textfont=dict(size=14, color=MUTED),
            hovertemplate=tr(
                lang,
                "<b>%{y}</b><br>Total deaths: %{x}<extra></extra>",
                "<b>%{y}</b><br>Все смерти: %{x}<extra></extra>",
            ),
            visible="legendonly",
        ))
        fig.update_layout(
            barmode="overlay",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="monospace", color=TEXT, size=14),
            margin=dict(l=10, r=40, t=10, b=40),
            xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, title=tr(lang, "Worlds", "Миры")),
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
                            <b style='color:{ACCENT_GOLD};'>{int(first_by[p])}</b> {tr(lang, 'first deaths', 'первых смертей')}
                            &nbsp;·&nbsp;
                            <b style='color:{ACCENT_GOLD};'>{int(total_by[p])}</b> {tr(lang, 'total', 'всего')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)

    # === Key insights (genuinely new info — not duplicated by the charts) ===
    # Reference total of distinct Java Edition death-message templates,
    # derived from assets/web/death_msg.html (snapshot of
    # minecraft.fandom.com/wiki/Death_messages, "== Java Edition ==" section).
    # Includes "Current" + "Removed" + "Unused" subsections — i.e., every
    # template Mojang's code base could broadcast. Re-run the parser in
    # assets/web/ if a new MC version adds new ones.
    JAVA_DEATH_MSG_TOTAL = 93

    section_header(tr(lang, "💡 Key Insights", "💡 Выводы"))
    if not failed.empty:
        msg_cnt = failed["first_death_message"].value_counts()
        unique_msgs = len(msg_cnt)
        only_once = msg_cnt[msg_cnt == 1]

        # All death events for this filtered subset (post + first deaths).
        filtered_deaths = data["deaths"][
            data["deaths"]["world_num"].isin(worlds["world_num"])
        ]
        n_deaths_total = len(filtered_deaths)
        total_active_min = (
            worlds["active_minutes"].fillna(0).astype(float).sum()
        )
        cadence_min = (total_active_min / n_deaths_total) if n_deaths_total else 0

        insights = []

        # 1. Narrative line on average run length (the one you said works).
        insights.append(
            tr(
                lang,
                f"⏱  An average run lasted "
                f"<span class='number'>{active_survival.mean():.0f} active minutes</span> "
                f"before someone died.",
                f"⏱  В среднем попытка держалась "
                f"<span class='number'>{active_survival.mean():.0f} активных минут</span> "
                f"до первой смерти.",
            )
        )

        # 2. Vocabulary line — N of 93 Java Edition templates we've hit,
        #    + list of the singletons.
        only_once_list = only_once.index.tolist()
        if only_once_list:
            preview = ", ".join(death_message_label(m, lang) for m in only_once_list[:3])
            if len(only_once_list) > 3:
                preview += tr(lang, f", … (+{len(only_once_list) - 3} more)", f", … (+{len(only_once_list) - 3} ещё)")
            singletons_clause = tr(
                lang,
                f" — <span class='number'>{len(only_once_list)}</span> of those "
                f"only happened once ({preview})",
                f" — <span class='number'>{len(only_once_list)}</span> из них "
                f"случились только один раз ({preview})",
            )
        else:
            singletons_clause = ""
        insights.append(
            tr(
                lang,
                f"🔢 We've encountered "
                f"<span class='number'>{unique_msgs}</span> of "
                f"<span class='number'>{JAVA_DEATH_MSG_TOTAL}</span> "
                f"distinct Minecraft Java Edition death messages{singletons_clause}.",
                f"🔢 Мы уже собрали "
                f"<span class='number'>{unique_msgs}</span> из "
                f"<span class='number'>{JAVA_DEATH_MSG_TOTAL}</span> "
                f"вариантов смертей Java Edition{singletons_clause}.",
            )
        )

        # 3. Death cadence — distinct from the median/mean cards above (which
        #    only count first-deaths). This is "all deaths per active minute".
        if n_deaths_total and total_active_min:
            insights.append(
                tr(
                    lang,
                    f"💀 Across <span class='number'>{total_active_min/60:.1f} hours</span> "
                    f"of active play we died <span class='number'>{n_deaths_total}</span> "
                    f"times — roughly one death every "
                    f"<span class='number'>{cadence_min:.1f} active minutes</span>.",
                    f"💀 За <span class='number'>{total_active_min/60:.1f} часа</span> "
                    f"активной игры мы умерли <span class='number'>{n_deaths_total}</span> "
                    f"раз — примерно одна смерть каждые "
                    f"<span class='number'>{cadence_min:.1f} активных минут</span>.",
                )
            )

        for ins in insights:
            st.markdown(f"<div class='insight-card'>{ins}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # === Browse worlds (uses filtered list) ===
    with st.expander(
        tr(
            lang,
            f"📋 Browse every world  ({n_total} after filters)",
            f"📋 Все миры  ({n_total} после фильтров)",
        )
    ):
        w = worlds.copy()
        w["outcome"] = w["outcome"].map(
            {"died": outcome_label("died", lang), "skipped": outcome_label("skipped", lang)}
        )
        # Per-row death message gets feminine forms when the dier is female.
        w["first_death_message"] = w.apply(
            lambda r: (
                death_message_label(
                    r["first_death_message"], lang, player=r["first_death_player"],
                )
                if pd.notna(r["first_death_message"]) else r["first_death_message"]
            ),
            axis=1,
        )
        w["first_death_category"] = w["first_death_category"].map(
            lambda c: cause_label(c, lang) if pd.notna(c) else c
        )
        w = w[[
            "world_num", "start_time", "outcome", "active_minutes", "wallclock_minutes",
            "first_death_player", "first_death_message", "first_death_category", "total_deaths",
        ]]
        w.columns = tr(
            lang,
            [
                "World #", "Started", "Outcome", "Active (min)", "Wall-clock (min)",
                "First died", "Death cause", "Category", "Total deaths",
            ],
            [
                "Мир #", "Создан", "Итог", "Активно (мин)", "По часам (мин)",
                "Кто погиб первым", "Причина смерти", "Категория", "Всего смертей",
            ],
        )
        st.dataframe(w, use_container_width=True, hide_index=True)

    st.markdown(f"<hr style='border-color:{BORDER};'>", unsafe_allow_html=True)


if __name__ == "__main__":
    build_app()
