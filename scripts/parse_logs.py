"""Parse Minecraft server logs into the CSVs that drive the dashboard.

Reads:  assets/logs/vanilla/*.log.gz, assets/logs/forge/*.log.gz, *.log
Writes: data/{summary,worlds,deaths,death_messages,players,pvp}.csv

Run from repo root:  python scripts/parse_logs.py

Read METHODOLOGY.md before changing anything. Each step is intentionally
explicit so the output is auditor-verifiable line-by-line.
"""
from __future__ import annotations

import csv
import gzip
import os
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_DIRS = [ROOT / "assets" / "logs" / "vanilla", ROOT / "assets" / "logs" / "forge"]
OUT_DIR = ROOT / "data"

# === Domain constants ===
PLAYERS = ["MurzichAI", "axantroff", "trofimova2002"]

# Hardcore mode was enabled at this wall-clock instant; worlds created before
# this should NOT be counted as part of the hardcore challenge.
# Source: chat history with axantroff on 2026-05-05 — server.properties flipped
# `hardcore=false` -> `hardcore=true` at this exact time before any death recorded.
HARDCORE_FROM = datetime(2026, 5, 5, 21, 37)

# === Regex catalog ===
# Two timestamp formats appear across our log eras:
#   Forge (with date):  [16May2026 17:32:10.657] [thread/LEVEL] [logger]: msg
#   Vanilla (no date):  [21:24:05] [ServerMain/LEVEL]: msg    <-- date taken from filename
TS_FORGE = re.compile(
    r"^\[(\d{2})([A-Za-z]{3})(\d{4})\s+(\d{2}):(\d{2}):(\d{2})\.\d+\]"
)
TS_VANILLA = re.compile(r"^\[(\d{2}):(\d{2}):(\d{2})\]")
MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
)}
FNAME_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")

# Official Minecraft death-message verbs.
# Source: https://minecraft.fandom.com/wiki/Death_messages
# Sorted longest-first so greedy regex matching prefers the most specific phrasing.
DEATH_VERBS = sorted([
    "was blown up", "was slain", "was killed", "was shot", "was impaled", "was pricked",
    "was doomed to fall", "was burnt to a crisp whilst fighting", "was burnt to a crisp",
    "was burned to a crisp while fighting", "was burned to death", "went up in flames",
    "walked into fire", "walked into a cactus", "walked into the danger zone",
    "walked into a wall while trying to escape",
    "fell from a high place", "fell off a ladder", "fell off some vines",
    "fell off some weeping vines", "fell off some twisting vines", "fell off scaffolding",
    "fell while climbing", "fell out of the water", "fell into a patch of fire",
    "fell into a patch of cacti", "fell out of the world",
    "drowned", "was drowned", "tried to swim in lava",
    "was squashed by a falling anvil", "was squashed by a falling block", "was squashed",
    "was struck by lightning",
    "starved to death", "suffocated in a wall", "suffocated", "withered away",
    "froze to death", "was frozen to death by",
    "died from dehydration", "died because of", "experienced kinetic energy",
    "went off with a bang", "was killed trying to hurt", "was killed by even more magic",
    "was killed by magic", "was killed by",
    "was poked to death by a sweet berry bush", "discovered the floor was lava", "blew up",
    "hit the ground too hard",
    "was crushed by a falling anvil", "was crushed by a falling block", "was crushed",
    "was pummeled by", "was killed by a falling block", "was killed by falling stalactite",
    "was impaled on a stalagmite", "died",
], key=len, reverse=True)

DEATH_RE = re.compile(r"(\w+) (" + "|".join(re.escape(v) for v in DEATH_VERBS) + r")(.*)$")
WORLD_RE = re.compile(r"creating new world|No existing world data, creating new world")
JOIN_RE = re.compile(r"(\w+) joined the game")
LEAVE_RE = re.compile(r"(\w+) left the game")
ADV_RE = re.compile(r"(\w+) has made the advancement \[([^\]]+)\]")

# Advancements that mark notable milestones. Names are official Mojang display titles.
# The list is used downstream for "time-to-X" stats; ordering reflects natural progression.
MILESTONES = [
    ("Stone Age",           "first cobblestone"),
    ("Acquire Hardware",    "first iron ingot"),
    ("Sweet Dreams",        "first sleep"),
    ("Isn't It Iron Pick",  "first iron pickaxe"),
    ("Suit Up",             "first armor"),
    ("Hot Stuff",           "first lava bucket"),
    ("Diamonds!",           "first diamond"),
    ("We Need to Go Deeper","first Nether portal"),
    ("A Terrible Fortress", "first Nether fortress"),
    ("Into Fire",           "first blaze rod"),
    ("Eye Spy",             "first ender eye"),
    ("The End?",            "reached The End"),
    ("Free the End",        "killed the Ender Dragon"),
]

# Categorization keywords. Order: PvP > Mob > Environment > Other.
# Note on "wither": appears in both lists by design. The Wither boss (mob) and
# the wither effect ("withered away" — environmental, e.g. suspicious stew) are
# distinct deaths but share the substring. We check Mob first because the boss
# is far more common in hardcore; if a "withered away" death ever appears in
# the data and is mis-categorized as Mob, narrow the Mob match to "wither boss"
# or remove "wither" from ENV_KEYWORDS.
MOB_KEYWORDS = [
    "creeper", "zombie", "husk", "skeleton", "enderman", "iron golem", "piglin", "ghast",
    "blaze", "wolf", "bear", "drowned", "wither", "spider", "witch", "vex", "phantom",
    "dragon", "warden", "vindicator", "pillager", "ravager", "silverfish", "endermite",
    "slime", "magma cube", "elder guardian", "guardian", "shulker",
]
ENV_KEYWORDS = [
    "fell", "ground too hard", "lava", "fire", "burn", "flame", "stalagmite", "stalactite",
    "cactus", "lightning", "drown", "froze", "frozen", "starve", "suffocate", "wither",
    "kinetic", "crushed", "squashed", "bang", "danger zone", "wall", "dehydration",
    "floor was lava",
]

# Guardrail: PvP attribution uses substring `by <PlayerName>`. If a tracked
# player's name collides with a vanilla entity display-name, every death by
# that mob would be mis-categorized as PvP. Names we use today are safe; this
# assert prevents a silent regression if someone joins as e.g. "Husk".
_VANILLA_ENTITY_TOKENS = {kw.title() for kw in MOB_KEYWORDS} | {"Player"}
assert not (set(PLAYERS) & _VANILLA_ENTITY_TOKENS), (
    f"Tracked player name collides with vanilla entity name: "
    f"{set(PLAYERS) & _VANILLA_ENTITY_TOKENS}. "
    f"Update PLAYERS or the PvP categorizer before parsing."
)


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


def parse_ts(line: str, fallback_date: datetime | None) -> datetime | None:
    m = TS_FORGE.match(line)
    if m:
        d, mn, y, hh, mm, ss = m.groups()
        return datetime(int(y), MONTHS[mn], int(d), int(hh), int(mm), int(ss))
    m = TS_VANILLA.match(line)
    if m and fallback_date:
        hh, mm, ss = (int(x) for x in m.groups())
        return fallback_date.replace(hour=hh, minute=mm, second=ss)
    return None


def file_date(path: Path) -> datetime | None:
    m = FNAME_DATE.search(path.name)
    return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def collect_log_paths() -> list[Path]:
    """Collect rotated logs in chronological order.

    Forge rotates two parallel families: the main log (`YYYY-MM-DD-N.log.gz`)
    and a verbose debug log (`debug-N.log.gz`). The debug log mirrors every
    INFO-level line from the main log, so reading both would double-count
    world creations, joins/leaves, advancements, and deaths. We use the main
    log as source-of-truth and skip the `debug-` family entirely.
    """
    paths: list[Path] = []
    for d in LOG_DIRS:
        if not d.is_dir():
            continue
        paths.extend(sorted(
            p for p in d.glob("*.log.gz") if not p.name.startswith("debug")
        ))
        latest = d / "latest.log"
        if latest.exists():
            paths.append(latest)
    paths.sort(key=lambda p: p.stat().st_mtime)
    return paths


def parse_events(paths: list[Path]) -> list[tuple]:
    """Returns sorted event list of tuples (timestamp, kind, who, payload, src_basename).

    Kinds:
      'W' — new world created
      'J' — player joined the game
      'L' — player left the game
      'D' — player died (payload = full death message minus the player name)
      'A' — player got an advancement (payload = display name without brackets)
    """
    events: list[tuple] = []
    for path in paths:
        # latest.log has no date in the filename — fall back to mtime, zeroed
        # to midnight (and to second-level precision) so we don't bleed
        # filesystem microsecond artifacts into derived CSVs.
        fd = file_date(path) or datetime.fromtimestamp(path.stat().st_mtime).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        opener = gzip.open if path.suffix == ".gz" else open
        last_ts = None
        with opener(path, "rt", errors="ignore") as f:
            for line in f:
                ts = parse_ts(line, fd)
                if ts is None:
                    continue
                # Vanilla logs lack date; if HH:MM:SS appears to wrap backward by >12h,
                # assume the log crossed midnight and bump the inferred date forward.
                if last_ts and ts < last_ts - timedelta(hours=12):
                    fd += timedelta(days=1)
                    ts += timedelta(days=1)
                last_ts = ts

                if WORLD_RE.search(line):
                    events.append((ts, "W", None, "", path.name))
                    continue
                m = DEATH_RE.search(line)
                if m and m.group(1) in PLAYERS:
                    full = (m.group(2) + m.group(3)).strip().rstrip(".")
                    events.append((ts, "D", m.group(1), full, path.name))
                    continue
                m = JOIN_RE.search(line)
                if m and m.group(1) in PLAYERS:
                    events.append((ts, "J", m.group(1), "", path.name))
                    continue
                m = LEAVE_RE.search(line)
                if m and m.group(1) in PLAYERS:
                    events.append((ts, "L", m.group(1), "", path.name))
                    continue
                m = ADV_RE.search(line)
                if m and m.group(1) in PLAYERS:
                    events.append((ts, "A", m.group(1), m.group(2), path.name))
    # Sort by (timestamp, then kind-order so a world boundary at the same instant
    # opens BEFORE deaths/joins/leaves are attributed). Advancements come after
    # joins so a "joined the game" + "made the advancement" pair on the same
    # second still attributes the join first.
    order = {"W": 0, "J": 1, "A": 2, "D": 3, "L": 4}
    events.sort(key=lambda e: (e[0], order[e[1]]))
    return events


def build_worlds(events: list[tuple]) -> list[dict]:
    """Partition events into worlds. A world spans [creation, next_creation).

    For the LAST world, `window_end` is capped at the most recent observed event
    rather than left open — otherwise an unclosed session in the current world
    would yield bogus multi-year "active" durations.
    """
    end_of_data = max((e[0] for e in events), default=datetime.utcnow())
    worlds: list[dict] = []
    cur: dict | None = None
    for ts, kind, who, payload, src in events:
        if kind == "W":
            if cur is not None:
                worlds.append(cur)
            cur = {"start": ts, "deaths": [], "sessions": [], "advancements": [], "src": src}
        elif cur is None:
            continue
        elif kind == "D":
            cur["deaths"].append((ts, who, payload, src))
        elif kind == "A":
            cur["advancements"].append((ts, who, payload, src))
        elif kind in ("J", "L"):
            cur["sessions"].append((ts, kind, who))
    if cur is not None:
        worlds.append(cur)
    for i, w in enumerate(worlds):
        next_start = worlds[i + 1]["start"] if i + 1 < len(worlds) else end_of_data
        w["deaths"].sort()
        # Window for first-death stats: world start → first death (or end of world).
        w["window_end"] = w["deaths"][0][0] if w["deaths"] else next_start
    return worlds


def active_minutes(sessions: list[tuple], window_start: datetime, window_end: datetime) -> float:
    """Return total wall-clock seconds within [window_start, window_end] during which
    AT LEAST ONE player was logged in. Computed as a union of per-player online
    intervals to avoid double-counting overlapping sessions.

    Handling of malformed event streams:
      * Two consecutive joins for the same player (no leave): the earlier join is
        closed at the next join's timestamp.
      * Leave without a matching join: ignored.
      * Join with no later leave: closed at window_end.
    """
    by_player: dict[str, list[tuple[datetime, datetime]]] = {p: [] for p in PLAYERS}
    open_at: dict[str, datetime] = {}

    for ts, kind, who in sorted(sessions, key=lambda s: s[0]):
        if kind == "J":
            if who in open_at:
                by_player[who].append((open_at[who], ts))
            open_at[who] = ts
        elif kind == "L":
            if who in open_at:
                by_player[who].append((open_at[who], ts))
                open_at.pop(who, None)
    for who, jt in open_at.items():
        by_player[who].append((jt, window_end))

    intervals: list[tuple[datetime, datetime]] = []
    for sessions_for in by_player.values():
        for s, e in sessions_for:
            s2 = max(s, window_start)
            e2 = min(e, window_end)
            if e2 > s2:
                intervals.append((s2, e2))

    intervals.sort()
    merged: list[list[datetime]] = []
    for s, e in intervals:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return sum((e - s).total_seconds() for s, e in merged) / 60


def write_csvs(worlds: list[dict]):
    OUT_DIR.mkdir(exist_ok=True)
    hc = [w for w in worlds if w["start"] >= HARDCORE_FROM]

    # worlds.csv
    with (OUT_DIR / "worlds.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "world_num", "start_time", "outcome", "first_death_at", "first_death_player",
            "first_death_message", "first_death_category", "total_deaths",
            "wallclock_minutes", "active_minutes", "source_log",
        ])
        for i, world in enumerate(hc, 1):
            am = active_minutes(world["sessions"], world["start"], world["window_end"])
            if world["deaths"]:
                ts, who, msg, _ = world["deaths"][0]
                wc = (ts - world["start"]).total_seconds() / 60
                w.writerow([
                    i, world["start"].isoformat(), "died", ts.isoformat(), who, msg,
                    categorize(msg), len(world["deaths"]), f"{wc:.1f}", f"{am:.1f}", world["src"],
                ])
            else:
                w.writerow([
                    i, world["start"].isoformat(), "skipped", "", "", "", "",
                    0, "", f"{am:.1f}", world["src"],
                ])

    # deaths.csv
    with (OUT_DIR / "deaths.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "world_num", "timestamp", "player", "death_message", "full_message",
            "is_first_in_world", "category", "source_log",
        ])
        for i, world in enumerate(hc, 1):
            for j, (ts, who, msg, src) in enumerate(world["deaths"]):
                w.writerow([
                    i, ts.isoformat(), who, msg, f"{who} {msg}",
                    "YES" if j == 0 else "NO", categorize(msg), src,
                ])

    # death_messages.csv (first deaths only — the metric that defines a failed run)
    msg_counts: Counter[str] = Counter()
    for world in hc:
        if world["deaths"]:
            msg_counts[world["deaths"][0][2]] += 1
    with (OUT_DIR / "death_messages.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["death_message", "count_first_deaths_only", "category", "example_full"])
        for msg, c in msg_counts.most_common():
            w.writerow([msg, c, categorize(msg), f"<player> {msg}"])

    # players.csv
    first: Counter[str] = Counter()
    total: Counter[str] = Counter()
    pvp_pairs: Counter[tuple[str, str]] = Counter()
    for world in hc:
        if world["deaths"]:
            first[world["deaths"][0][1]] += 1
            for _, who, msg, _ in world["deaths"]:
                total[who] += 1
                for p in PLAYERS:
                    if f"by {p}" in msg:
                        pvp_pairs[(p, who)] += 1
    with (OUT_DIR / "players.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["player", "first_deaths", "total_deaths", "pvp_kills_on_others"])
        for p in PLAYERS:
            kills = sum(c for (killer, _), c in pvp_pairs.items() if killer == p)
            w.writerow([p, first[p], total[p], kills])

    # pvp.csv
    with (OUT_DIR / "pvp.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["killer", "victim", "count"])
        for (killer, victim), c in sorted(pvp_pairs.items(), key=lambda x: -x[1]):
            w.writerow([killer, victim, c])

    # advancements.csv — one row per advancement event, tagged with world.
    # Captures the FIRST time each (world, player, advancement) triple appears
    # so re-broadcasts on relogin don't inflate counts.
    seen_per_world: set[tuple[int, str, str]] = set()
    adv_rows: list[tuple] = []
    n_unique_advancements: set[str] = set()
    for i, world in enumerate(hc, 1):
        for ts, who, name, src in world["advancements"]:
            key = (i, who, name)
            if key in seen_per_world:
                continue
            seen_per_world.add(key)
            n_unique_advancements.add(name)
            mins = (ts - world["start"]).total_seconds() / 60
            adv_rows.append((i, ts.isoformat(), who, name, f"{mins:.1f}", src))
    with (OUT_DIR / "advancements.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "world_num", "timestamp", "player", "advancement",
            "minutes_into_run", "source_log",
        ])
        w.writerows(adv_rows)

    # summary.csv
    n_total = len(hc)
    n_failed = sum(1 for x in hc if x["deaths"])
    n_skipped = n_total - n_failed
    # Sum the *rounded-to-1-decimal* per-world values so summary.csv matches
    # what an auditor would get from `awk` over worlds.csv. (Summing the raw
    # seconds and rounding once at the end produces a ~0.2 min drift.)
    total_active = sum(
        round(active_minutes(w["sessions"], w["start"], w["window_end"]), 1) for w in hc
    )
    with (OUT_DIR / "summary.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerow(["hardcore_from", HARDCORE_FROM.isoformat()])
        w.writerow(["total_worlds_attempted", n_total])
        w.writerow(["worlds_died", n_failed])
        w.writerow(["worlds_skipped", n_skipped])
        w.writerow(["failure_rate_pct", f"{100*n_failed/n_total:.1f}"])
        w.writerow(["total_deaths", sum(total.values())])
        w.writerow(["unique_death_messages", len(msg_counts)])
        w.writerow(["total_active_minutes", f"{total_active:.1f}"])
        w.writerow(["total_active_hours", f"{total_active/60:.1f}"])
        w.writerow(["total_advancement_events", len(adv_rows)])
        w.writerow(["unique_advancements", len(n_unique_advancements)])

    return {
        "worlds": n_total, "failed": n_failed, "skipped": n_skipped,
        "deaths": sum(total.values()), "unique_msgs": len(msg_counts),
        "active_h": total_active / 60,
        "adv_events": len(adv_rows), "adv_unique": len(n_unique_advancements),
    }


def main():
    paths = collect_log_paths()
    print(f"Reading {len(paths)} log files...")
    events = parse_events(paths)
    print(f"Parsed {len(events)} events ({sum(1 for e in events if e[1]=='W')} world creations, "
          f"{sum(1 for e in events if e[1]=='D')} deaths, "
          f"{sum(1 for e in events if e[1] in ('J','L'))} session events).")

    worlds = build_worlds(events)
    print(f"Partitioned into {len(worlds)} worlds total "
          f"({sum(1 for w in worlds if w['start'] >= HARDCORE_FROM)} hardcore).")

    stats = write_csvs(worlds)
    print(
        f"\nWrote 7 CSVs to {OUT_DIR.relative_to(ROOT)}:\n"
        f"  worlds_total       = {stats['worlds']}\n"
        f"  worlds_failed      = {stats['failed']}\n"
        f"  worlds_skipped     = {stats['skipped']}\n"
        f"  total_deaths       = {stats['deaths']}\n"
        f"  unique_msgs        = {stats['unique_msgs']}\n"
        f"  advancement_events = {stats['adv_events']}\n"
        f"  unique_advancements= {stats['adv_unique']}\n"
        f"  active_hours       = {stats['active_h']:.1f}"
    )


if __name__ == "__main__":
    main()
