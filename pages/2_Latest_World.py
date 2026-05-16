"""Page 2 — Latest World deep dive.

Renders fun stats from the snapshot of the currently-active hardcore world.
This is the only world (out of 44) for which detailed per-player stats survived.
Source CSVs: data/live_stats_summary.csv, data/live_stats_detail.csv,
data/live_advancements.csv (produced by scripts/parse_snapshot.py).
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from i18n import (
    advancement_id_label,
    item_label,
    language_selector,
    ru_verb,
    tr,
    unit_minutes,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

PLAYERS = ["MurzichAI", "axantroff", "trofimova2002"]
PLAYER_COLOR = {
    "MurzichAI": "#DC2626",
    "axantroff": "#3DD5F3",
    "trofimova2002": "#7CB342",
}

ACCENT_GOLD = "#FFAA00"
GRASS_GREEN = "#7CB342"
LAVA_ORANGE = "#FF8C1A"
DIAMOND = "#3DD5F3"
BG_DARK = "#1B1D24"
SURFACE = "#2A2D36"
BORDER = "#3D4148"
TEXT = "#F5F5F5"
MUTED = "#9CA3AF"

def hero_labels(lang):
    # Tuple shape: (label, csv_column_key, unit_suffix, optional_help_tooltip)
    return [
        (tr(lang, "⏱  Time Played", "⏱  Время игры"), "play_minutes", unit_minutes(lang), None),
        (tr(lang, "🚶  Walked", "🚶  Пешком"), "walk_m", "m", None),
        (tr(lang, "🏃  Sprinted", "🏃  Бегом"), "sprint_m", "m", None),
        (
            tr(lang, "🪂  Air Time", "🪂  В воздухе"),
            "fly_m",
            "m",
            tr(
                lang,
                "Cumulative cm spent airborne — jumping, falling, gliding. Not elytra-specific.",
                "Суммарная дистанция в воздухе: прыжки, падения, полет. Это не только элитры.",
            ),
        ),
        (tr(lang, "⛏️  Blocks Mined", "⛏️  Блоков добыто"), "blocks_mined_total", "", None),
        (tr(lang, "⚔️  Mobs Killed", "⚔️  Мобов убито"), "mob_kills_total", "", None),
        (
            tr(lang, "🔨  Items Crafted", "🔨  Предметов создано"),
            "items_crafted_total",
            "",
            tr(
                lang,
                "Minecraft counts crafted items by *output count*, not unique recipes. "
                "Crafting one stack of sticks (4 planks → 4 sticks) adds 4 here — that's why "
                "the number can hit the tens of thousands.",
                "Minecraft считает созданные предметы по количеству результата, а не по уникальным рецептам. "
                "Один крафт палок из досок дает +4, поэтому число может улетать в десятки тысяч.",
            ),
        ),
        (tr(lang, "📦  Items Picked Up", "📦  Предметов поднято"), "items_picked_up_total", "", None),
        (tr(lang, "🛏️  Times Slept", "🛏️  Раз спал"), "sleep_count", "", None),
        (tr(lang, "🤸  Jumps", "🤸  Прыжков"), "jumps", "", None),
        (
            tr(lang, "💥  Damage Dealt", "💥  Урона нанесено"),
            "damage_dealt_hearts",
            "♥",
            tr(
                lang,
                "Damage dealt to mobs, in hearts. Minecraft stores this as integer tenths-of-hearts; "
                "we divide by 10 for display.",
                "Урон мобам в сердцах. Minecraft хранит его в десятых долях сердца, здесь значение делится на 10.",
            ),
        ),
        (
            tr(lang, "🩸  Damage Taken", "🩸  Урона получено"),
            "damage_taken_hearts",
            "♥",
            tr(
                lang,
                "Damage absorbed by the player, in hearts. Same divide-by-10 conversion.",
                "Полученный урон в сердцах. Та же конвертация: деление на 10.",
            ),
        ),
    ]


@st.cache_data
def load_snapshot():
    summary = pd.read_csv(DATA_DIR / "live_stats_summary.csv")
    detail = pd.read_csv(DATA_DIR / "live_stats_detail.csv")
    advs = pd.read_csv(DATA_DIR / "live_advancements.csv")
    return summary, detail, advs


def section_header(title: str, sub: str = ""):
    st.markdown(f"### {title}")
    if sub:
        st.caption(sub)


def fmt_num(v) -> str:
    """Compact number display: 1.2k, 5.2 km, 47%, etc. Keeps things readable in cards."""
    try:
        n = float(v)
    except (TypeError, ValueError):
        return str(v)
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    if n >= 100 or n.is_integer():
        return f"{int(n) if n.is_integer() else n:.0f}"
    return f"{n:.1f}"


def build_page():
    st.set_page_config(
        page_title="Latest World — Hardcore Chronicles",
        page_icon="🏕️",
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
            font-size: 2rem; color: {ACCENT_GOLD}; font-weight: 800;
            text-shadow: 0 0 10px rgba(255,170,0,0.2);
        }}
        div[data-testid="stMetricLabel"] {{ font-size: 0.85rem; color: {TEXT}; font-weight: 600; }}
        div[data-testid="stMetric"] {{
            background: {SURFACE};
            border: 2px solid {BORDER};
            border-radius: 6px;
            padding: 14px 12px;
        }}
        section[data-testid="stSidebar"] {{ background-color: {SURFACE}; }}
        .stPlotlyChart {{ background-color: transparent; }}
        hr {{ border-color: {BORDER} !important; }}
        .player-card {{
            background: {SURFACE};
            border-radius: 6px;
            padding: 14px 18px;
            margin: 4px 0;
        }}
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
    summary, detail, advs = load_snapshot()

    st.markdown(tr(lang, "# 🏕️ THE LATEST WORLD", "# 🏕️ ТЕКУЩИЙ МИР"))

    st.markdown(f"<hr style='border-color:{BORDER};'>", unsafe_allow_html=True)

    # === Hero stats: per-player columns ===
    section_header(
        tr(lang, "👥 Tale of the Tape", "👥 Кто чем занимался"),
        tr(lang, "Side-by-side counters for each player in this world.", "Статы каждого игрока в этом мире рядом."),
    )

    cols = st.columns(len(PLAYERS))
    summary_by_player = summary.set_index("player")
    for col, p in zip(cols, PLAYERS):
        if p not in summary_by_player.index:
            col.warning(f"{p} has no stats in this world.")
            continue
        row = summary_by_player.loc[p]
        with col:
            st.markdown(
                f"""
                <div style='background:{SURFACE};border:3px solid {PLAYER_COLOR[p]};
                            border-radius:8px;padding:12px 16px;text-align:center;
                            margin-bottom:14px;'>
                    <div style='color:{PLAYER_COLOR[p]};font-weight:800;font-size:1.3rem;
                                letter-spacing:0.03em;'>{p}</div>
                    <div style='color:{MUTED};font-size:0.85rem;margin-top:4px;'>
                        {fmt_num(row["play_minutes"])} {unit_minutes(lang)} {tr(lang, 'played', 'в игре')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # 2-col grid of compact metrics inside the player card
            mg1, mg2 = st.columns(2)
            for i, (label, col_key, unit, help_text) in enumerate(hero_labels(lang)):
                val = row[col_key]
                txt = f"{fmt_num(val)}{(' ' + unit) if unit else ''}"
                (mg1 if i % 2 == 0 else mg2).metric(label, txt, help=help_text)

    st.markdown("<br>", unsafe_allow_html=True)

    # === Movement breakdown ===
    section_header(
        tr(lang, "🧭 Movement Profile", "🧭 Как передвигались"),
        tr(
            lang,
            "How each player spent their travel distance. “Air” = jumping / falling time (not necessarily elytra).",
            "Из чего складывалась дистанция. 'В воздухе' = прыжки, падения и полет, не только элитры.",
        ),
    )

    move_cols = ["walk_m", "sprint_m", "fly_m", "fall_m", "walk_on_water_m", "walk_under_water_m", "crouch_m"]
    move_labels = {
        "walk_m": tr(lang, "Walk", "Пешком"),
        "sprint_m": tr(lang, "Sprint", "Бегом"),
        "fly_m": tr(lang, "Air", "В воздухе"),
        "fall_m": tr(lang, "Fall", "Падение"),
        "walk_on_water_m": tr(lang, "On Water", "По воде"),
        "walk_under_water_m": tr(lang, "Under Water", "Под водой"),
        "crouch_m": tr(lang, "Sneak", "Крадучись"),
    }
    move_df = summary[["player"] + move_cols].melt(id_vars="player", var_name="mode", value_name="meters")
    move_df["mode"] = move_df["mode"].map(move_labels)
    # Order players consistently and modes by total distance.
    mode_order = move_df.groupby("mode")["meters"].sum().sort_values(ascending=False).index.tolist()

    move_fig = px.bar(
        move_df,
        x="meters",
        y="player",
        color="mode",
        orientation="h",
        category_orders={"player": PLAYERS[::-1], "mode": mode_order},
        color_discrete_sequence=[
            GRASS_GREEN,
            LAVA_ORANGE,
            ACCENT_GOLD,
            "#DC2626",
            DIAMOND,
            "#7C3AED",
            MUTED,
        ],
        labels={"meters": tr(lang, "Meters", "Метры"), "player": ""},
    )
    move_fig.update_traces(marker_line_color=BG_DARK, marker_line_width=1)
    move_fig.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="monospace", color=TEXT, size=13),
        height=300,
        margin=dict(l=10, r=40, t=10, b=40),
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.30,
            xanchor="right",
            x=1,
            bgcolor=SURFACE,
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(color=TEXT),
        ),
    )
    st.plotly_chart(move_fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # === Per-category "what we did most" bars ===
    # NOTE: this section used to be titled "Top of the Leaderboards" with a
    # trophy icon. task.md §4 #2 explicitly forbids leaderboard/competition
    # framing, so it was renamed to read as "what the group did", not "who is
    # winning". Keep the framing neutral if you change anything here.
    section_header(
        tr(lang, "📊 What We Did Most", "📊 Что мы делали чаще всего"),
        tr(
            lang,
            "Per-category counters across all three players by default. "
            "Use the selector below to look at one player at a time.",
            "По умолчанию суммарно по всем троим. Переключатель ниже показывает одного игрока.",
        ),
    )

    all_players_label = tr(lang, "All Players", "Все игроки")
    # Selector: "All Players" (sum across) or one specific player.
    leader_view = st.radio(
        tr(lang, "View", "Вид"),
        options=["all"] + PLAYERS,
        index=0,
        format_func=lambda value: all_players_label if value == "all" else value,
        label_visibility="collapsed",
        horizontal=True,
        key="leaderboard_view",
    )

    # When showing one player: tint every chart with that player's color so the
    # perspective is unmistakable. When showing totals: keep the original six
    # distinct colors for visual variety.
    is_player_view = leader_view in PLAYERS
    player_tint = PLAYER_COLOR.get(leader_view) if is_player_view else None

    def top_chart(cat: str, title: str, color: str, n: int = 6):
        df = detail
        if is_player_view:
            df = df[df["player"] == leader_view]
        d = df[df["category"] == cat].groupby("item")["count"].sum().sort_values(ascending=False).head(n).reset_index()
        d = d.sort_values("count", ascending=True)
        d["display_item"] = d["item"].map(lambda x: item_label(x, lang))
        if d.empty:
            # Empty category for this player — render a placeholder rather than
            # a broken chart. trofimova2002 has only 1 mob kill, for example.
            st.markdown(
                f"<div style='background:{SURFACE};border:2px solid {BORDER};"
                f"border-radius:6px;padding:18px;text-align:center;"
                f"color:{MUTED};height:200px;display:flex;flex-direction:column;"
                f"justify-content:center;'>"
                f"<div style='color:{ACCENT_GOLD};font-size:15px;font-weight:700;"
                f"margin-bottom:8px;'>{title}</div>"
                f"<div style='font-size:0.9rem;'>{tr(lang, 'nothing here', 'пусто')}</div></div>",
                unsafe_allow_html=True,
            )
            return
        bar_color = player_tint or color
        fig = go.Figure(
            data=[
                go.Bar(
                    x=d["count"],
                    y=d["display_item"],
                    orientation="h",
                    marker=dict(color=bar_color, line=dict(color=BG_DARK, width=2)),
                    text=d["count"],
                    textposition="outside",
                    textfont=dict(size=13, color=TEXT),
                    hovertemplate="<b>%{y}</b><br>%{x}<extra></extra>",
                )
            ]
        )
        max_x = float(d["count"].max())
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="monospace", color=TEXT, size=12),
            height=max(220, 36 * len(d) + 60),
            margin=dict(l=10, r=60, t=30, b=20),
            title=dict(text=title, x=0.0, font=dict(color=ACCENT_GOLD, size=15)),
            xaxis=dict(gridcolor=BORDER, range=[0, max_x * 1.25]),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)

    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        top_chart("mined", tr(lang, "⛏️ Most Mined", "⛏️ Больше всего добывали"), GRASS_GREEN)
    with lc2:
        top_chart("killed", tr(lang, "⚔️ Most Killed", "⚔️ Больше всего убивали"), "#DC2626")
    with lc3:
        top_chart("used", tr(lang, "🔧 Most Used", "🔧 Больше всего использовали"), ACCENT_GOLD)

    lc4, lc5, lc6 = st.columns(3)
    with lc4:
        top_chart("crafted", tr(lang, "🛠️ Most Crafted", "🛠️ Больше всего крафтили"), LAVA_ORANGE)
    with lc5:
        top_chart("picked_up", tr(lang, "📥 Most Picked Up", "📥 Больше всего поднимали"), DIAMOND)
    with lc6:
        top_chart("dropped", tr(lang, "📤 Most Dropped", "📤 Больше всего выбрасывали"), MUTED)

    st.markdown("<br>", unsafe_allow_html=True)

    # === Advancements per player ===
    section_header(
        tr(lang, "🏅 Achievements In This World", "🏅 Достижения в этом мире"),
        tr(
            lang,
            "Non-recipe advancements unlocked by each player in the live world. "
            "Each player progresses independently — sleeping, smelting iron, etc. "
            "are all individual milestones.",
            "Достижения без рецептов, полученные каждым игроком. Сон, железо и другие шаги считаются отдельно для каждого.",
        ),
    )

    completed = advs[advs["done"] == "YES"].copy()

    if completed.empty:
        st.info(tr(lang, "No advancements completed yet in this world.", "В этом мире пока нет завершенных достижений."))
    else:
        # Pretty up the advancement IDs:  minecraft:adventure/sleep_in_bed -> Adventure / Sleep In Bed
        def pretty(a):
            a = a.replace("minecraft:", "")
            cat, _, name = a.partition("/")
            name = name.replace("_", " ").title() if name else ""
            return f"{cat.title()}", f"{name}"

        completed[["category", "name"]] = completed["advancement_id"].apply(lambda a: pd.Series(pretty(a)))
        completed["name"] = completed.apply(
            lambda r: advancement_id_label(r["advancement_id"], r["name"], lang),
            axis=1,
        )
        completed["category"] = completed["category"].replace(
            {
                "Adventure": tr(lang, "🗺️ Adventure", "🗺️ Приключения"),
                "Husbandry": tr(lang, "🌾 Husbandry", "🌾 Сельское хозяйство"),
                "Story": tr(lang, "📖 Story", "📖 Minecraft"),
                "Nether": tr(lang, "🔥 Nether", "🔥 Незер"),
                "End": tr(lang, "🐉 End", "🐉 Край"),
            }
        )

        ach_cols = st.columns(len(PLAYERS))
        for col, p in zip(ach_cols, PLAYERS):
            sub = completed[completed["player"] == p].copy()
            with col:
                st.markdown(
                    f"<div style='color:{PLAYER_COLOR[p]};font-weight:800;"
                    f"text-align:center;font-size:1.05rem;letter-spacing:0.03em;"
                    f"padding:8px;border-bottom:2px solid {PLAYER_COLOR[p]};"
                    f"margin-bottom:8px;'>{p} — {len(sub)} {tr(lang, 'unlocked', 'получено')}</div>",
                    unsafe_allow_html=True,
                )
                if sub.empty:
                    st.caption(tr(lang, "Nothing yet.", "Пока ничего."))
                    continue
                # Group by category for compact display
                for cat in sub["category"].drop_duplicates().tolist():
                    items = sub[sub["category"] == cat]["name"].tolist()
                    st.markdown(
                        f"<div class='player-card'>"
                        f"<div style='color:{ACCENT_GOLD};font-size:0.85rem;"
                        f"font-weight:700;margin-bottom:4px;'>{cat}</div>"
                        f"<div style='color:{TEXT};font-size:0.85rem;line-height:1.45;'>"
                        f"{' · '.join(items)}"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )

    st.markdown("<br>", unsafe_allow_html=True)

    # === Auto-generated fun facts ===
    section_header(tr(lang, "✨ Notable Stats", "✨ Заметные факты"))

    s = summary.set_index("player")
    facts = []

    def detail_count(player, category, item=None, contains=None):
        rows = detail[(detail["player"] == player) & (detail["category"] == category)]
        if item is not None:
            rows = rows[rows["item"] == item]
        if contains is not None:
            rows = rows[rows["item"].str.contains(contains, na=False)]
        return int(rows["count"].sum())

    murzich_trades = detail_count("MurzichAI", "custom", item="traded_with_villager")
    murzich_sticks = detail_count("MurzichAI", "crafted", item="stick")
    facts.append(
        tr(
            lang,
            f"🧾 <b>MurzichAI</b> traded with villagers "
            f"<span class='number'>{murzich_trades:,}</span> times and crafted "
            f"<span class='number'>{murzich_sticks:,}</span> sticks.",
            f"🧾 <b>MurzichAI</b> сделал "
            f"<span class='number'>{murzich_trades:,}</span> сделок с крестьянами и скрафтил "
            f"<span class='number'>{murzich_sticks:,}</span> палок.",
        )
    )

    trofimova_saplings = detail_count("trofimova2002", "used", contains="sapling")
    facts.append(
        tr(
            lang,
            f"🌱 <b>trofimova2002</b> planted "
            f"<span class='number'>{trofimova_saplings:,}</span> saplings.",
            f"🌱 <b>trofimova2002</b> посадила "
            f"<span class='number'>{trofimova_saplings:,}</span> саженцев.",
        )
    )

    # Biggest walker / sprinter / flyer
    walk_leader = s["walk_m"].idxmax()
    facts.append(
        tr(
            lang,
            f"🚶 <b>{walk_leader}</b> walked the most — "
            f"<span class='number'>{s.loc[walk_leader, 'walk_m']:.0f} m</span> "
            f"({s.loc[walk_leader, 'walk_m'] / 1000:.1f} km on foot).",
            f"🚶 <b>{walk_leader}</b> больше всех "
            f"{ru_verb(walk_leader, 'ходил', 'ходила')} пешком — "
            f"<span class='number'>{s.loc[walk_leader, 'walk_m']:.0f} м</span> "
            f"({s.loc[walk_leader, 'walk_m'] / 1000:.1f} км).",
        )
    )
    fly_leader = s["fly_m"].idxmax()
    facts.append(
        tr(
            lang,
            f"🪂 <b>{fly_leader}</b> spent the most time in the air — "
            f"<span class='number'>{s.loc[fly_leader, 'fly_m']:.0f} m</span> "
            f"(falling, jumping, or otherwise airborne).",
            f"🪂 <b>{fly_leader}</b> больше всех "
            f"{ru_verb(fly_leader, 'провел', 'провела')} в воздухе — "
            f"<span class='number'>{s.loc[fly_leader, 'fly_m']:.0f} м</span> "
            f"(прыжки, падения и прочее).",
        )
    )

    # Combat efficiency
    fighter = s["mob_kills_total"].idxmax()
    facts.append(
        tr(
            lang,
            f"⚔️ <b>{fighter}</b> killed the most mobs — "
            f"<span class='number'>{int(s.loc[fighter, 'mob_kills_total'])}</span> in total.",
            f"⚔️ <b>{fighter}</b> {ru_verb(fighter, 'убил', 'убила')} больше всего мобов — "
            f"<span class='number'>{int(s.loc[fighter, 'mob_kills_total'])}</span> всего.",
        )
    )
    most_dmg = s["damage_dealt_hearts"].idxmax()
    most_hurt = s["damage_taken_hearts"].idxmax()
    if most_dmg == most_hurt:
        facts.append(
            tr(
                lang,
                f"💥 <b>{most_dmg}</b> dealt the most damage "
                f"(<span class='number'>{s.loc[most_dmg, 'damage_dealt_hearts']:.1f}♥</span>) "
                f"and also took the most "
                f"(<span class='number'>{s.loc[most_dmg, 'damage_taken_hearts']:.1f}♥</span>).",
                f"💥 <b>{most_dmg}</b> {ru_verb(most_dmg, 'нанес', 'нанесла')} больше всего урона "
                f"(<span class='number'>{s.loc[most_dmg, 'damage_dealt_hearts']:.1f}♥</span>) "
                f"и {ru_verb(most_dmg, 'сам получил', 'сама получила')} больше всех "
                f"(<span class='number'>{s.loc[most_dmg, 'damage_taken_hearts']:.1f}♥</span>).",
            )
        )
    else:
        facts.append(
            tr(
                lang,
                f"💥 <b>{most_dmg}</b> dealt the most damage "
                f"(<span class='number'>{s.loc[most_dmg, 'damage_dealt_hearts']:.1f}♥</span>) "
                f"while <b>{most_hurt}</b> took the most "
                f"(<span class='number'>{s.loc[most_hurt, 'damage_taken_hearts']:.1f}♥</span>).",
                f"💥 <b>{most_dmg}</b> {ru_verb(most_dmg, 'нанес', 'нанесла')} больше всего урона "
                f"(<span class='number'>{s.loc[most_dmg, 'damage_dealt_hearts']:.1f}♥</span>), "
                f"а <b>{most_hurt}</b> {ru_verb(most_hurt, 'получил', 'получила')} больше всех "
                f"(<span class='number'>{s.loc[most_hurt, 'damage_taken_hearts']:.1f}♥</span>).",
            )
        )

    # Looter
    looter = s["open_chest"].idxmax()
    facts.append(
        tr(
            lang,
            f"📦 <b>{looter}</b> opened <span class='number'>{int(s.loc[looter, 'open_chest'])}</span> chests.",
            f"📦 <b>{looter}</b> {ru_verb(looter, 'открыл', 'открыла')} "
            f"<span class='number'>{int(s.loc[looter, 'open_chest'])}</span> сундуков.",
        )
    )

    # Sleeper
    sleeper = s["sleep_count"].idxmax()
    facts.append(
        tr(
            lang,
            f"🛏️ <b>{sleeper}</b> slept "
            f"<span class='number'>{int(s.loc[sleeper, 'sleep_count'])}</span> "
            f"nights through — the most-rested of the group.",
            f"🛏️ <b>{sleeper}</b> {ru_verb(sleeper, 'проспал', 'проспала')} "
            f"<span class='number'>{int(s.loc[sleeper, 'sleep_count'])}</span> "
            f"ночей — {ru_verb(sleeper, 'самый отдохнувший', 'самая отдохнувшая')} в группе.",
        )
    )

    # Tool destroyer
    breaker = s["tools_broken"].idxmax()
    facts.append(
        tr(
            lang,
            f"🔨 <b>{breaker}</b> wore through <span class='number'>{int(s.loc[breaker, 'tools_broken'])}</span> tools.",
            f"🔨 <b>{breaker}</b> {ru_verb(breaker, 'сломал', 'сломала')} "
            f"<span class='number'>{int(s.loc[breaker, 'tools_broken'])}</span> инструментов.",
        )
    )

    # Jumper
    jumper = s["jumps"].idxmax()
    facts.append(
        tr(
            lang,
            f"🤸 <b>{jumper}</b> jumped <span class='number'>{int(s.loc[jumper, 'jumps']):,}</span> times.",
            f"🤸 <b>{jumper}</b> {ru_verb(jumper, 'прыгнул', 'прыгнула')} "
            f"<span class='number'>{int(s.loc[jumper, 'jumps']):,}</span> раз.",
        )
    )

    for f in facts:
        st.markdown(f"<div class='insight-card'>{f}</div>", unsafe_allow_html=True)

    st.markdown(f"<hr style='border-color:{BORDER};'>", unsafe_allow_html=True)


if __name__ == "__main__":
    build_page()
