"""Flatten one Minecraft world snapshot into CSVs the dashboard can consume.

Reads:  assets/snapshots/live-world/players/{stats,advancements}/*.json
Writes: data/live_stats_summary.csv      — one row per player, key counters
        data/live_stats_detail.csv       — long-form (player, category, item, count)
        data/live_advancements.csv       — one row per (player, advancement, done)

The 'live world' is the currently-active hardcore world hosted by axantroff.
It is the only world out of 44 for which per-player stats survived (older
worlds were deleted on reroll before any backup). All non-recipe advancements
are exported; recipe unlocks are skipped because they fire on every craft and
would drown out the interesting story/adventure/nether/end achievements.

Run from repo root:  python scripts/parse_snapshot.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "assets" / "snapshots" / "live-world"
OUT_DIR = ROOT / "data"

# Offline-mode UUIDs (deterministic MD5 of OfflinePlayer:<name>).
UUID_TO_PLAYER = {
    "b640b54b-74f4-332d-a6ca-62f3f8849bfd": "axantroff",
    "9f7deb4a-782c-3f6b-8366-625193e5854b": "MurzichAI",
    "0667e348-1378-36ef-a6c1-0132de3090b4": "trofimova2002",
}

# Minecraft stores time as game ticks (20 ticks = 1 wall-clock second).
TICKS_PER_SEC = 20
# Distances in `minecraft:custom` are stored in centimeters.
CM_PER_M = 100


def load_stats(uuid: str) -> dict:
    path = SNAP / "players" / "stats" / f"{uuid}.json"
    with path.open() as f:
        return json.load(f).get("stats", {})


def load_advancements(uuid: str) -> dict:
    path = SNAP / "players" / "advancements" / f"{uuid}.json"
    with path.open() as f:
        return json.load(f)


def summarize(stats: dict) -> dict:
    """Pick out the counters most useful for a 'fun facts' panel.

    All distance counters are converted from cm → m. Time counters from ticks → minutes.
    """
    custom = stats.get("minecraft:custom", {})
    mined = stats.get("minecraft:mined", {})
    killed = stats.get("minecraft:killed", {})
    used = stats.get("minecraft:used", {})
    crafted = stats.get("minecraft:crafted", {})
    picked_up = stats.get("minecraft:picked_up", {})
    dropped = stats.get("minecraft:dropped", {})
    broken = stats.get("minecraft:broken", {})
    killed_by = stats.get("minecraft:killed_by", {})

    return {
        # core
        "play_minutes": custom.get("minecraft:play_time", 0) / TICKS_PER_SEC / 60,
        "deaths": custom.get("minecraft:deaths", 0),
        "jumps": custom.get("minecraft:jump", 0),
        # distance (m)
        "walk_m": custom.get("minecraft:walk_one_cm", 0) / CM_PER_M,
        "sprint_m": custom.get("minecraft:sprint_one_cm", 0) / CM_PER_M,
        "fly_m": custom.get("minecraft:fly_one_cm", 0) / CM_PER_M,
        "fall_m": custom.get("minecraft:fall_one_cm", 0) / CM_PER_M,
        "swim_m": custom.get("minecraft:swim_one_cm", 0) / CM_PER_M,
        "boat_m": custom.get("minecraft:boat_one_cm", 0) / CM_PER_M,
        "crouch_m": custom.get("minecraft:crouch_one_cm", 0) / CM_PER_M,
        "walk_on_water_m": custom.get("minecraft:walk_on_water_one_cm", 0) / CM_PER_M,
        "walk_under_water_m": custom.get("minecraft:walk_under_water_one_cm", 0) / CM_PER_M,
        # combat
        "damage_dealt_hearts": custom.get("minecraft:damage_dealt", 0) / 10,
        "damage_taken_hearts": custom.get("minecraft:damage_taken", 0) / 10,
        "mob_kills_total": sum(killed.values()),
        "killed_by_count": sum(killed_by.values()),
        # progression
        "blocks_mined_total": sum(mined.values()),
        "items_used_total": sum(used.values()),
        "items_crafted_total": sum(crafted.values()),
        "items_picked_up_total": sum(picked_up.values()),
        "items_dropped_total": sum(dropped.values()),
        "tools_broken": sum(broken.values()),
        # life events
        "sleep_count": custom.get("minecraft:sleep_in_bed", 0),
        "time_since_rest_min":
            custom.get("minecraft:time_since_rest", 0) / TICKS_PER_SEC / 60,
        "time_since_death_min":
            custom.get("minecraft:time_since_death", 0) / TICKS_PER_SEC / 60,
        # interactions
        "interact_furnace": custom.get("minecraft:interact_with_furnace", 0),
        "interact_crafting_table": custom.get("minecraft:interact_with_crafting_table", 0),
        "open_chest": custom.get("minecraft:open_chest", 0),
        # variety counters
        "unique_blocks_mined": len(mined),
        "unique_mobs_killed": len(killed),
        "unique_items_used": len(used),
        "unique_items_crafted": len(crafted),
    }


def write_csvs():
    OUT_DIR.mkdir(exist_ok=True)

    # --- per-player summary ---
    rows = []
    detail_rows = []
    adv_rows = []
    for uuid, player in UUID_TO_PLAYER.items():
        try:
            stats = load_stats(uuid)
        except FileNotFoundError:
            print(f"  skipping {player}: no stats file")
            continue
        summary = summarize(stats)
        summary["player"] = player
        rows.append(summary)

        for cat, items in stats.items():
            cat_short = cat.replace("minecraft:", "")
            for item, count in items.items():
                detail_rows.append({
                    "player": player,
                    "category": cat_short,
                    "item": item.replace("minecraft:", ""),
                    "count": count,
                })

        try:
            advancements = load_advancements(uuid)
        except FileNotFoundError:
            continue
        for adv_id, state in advancements.items():
            # Skip recipe unlocks — they fire on every craft and aren't player-facing.
            if adv_id.startswith("minecraft:recipes/"):
                continue
            if not isinstance(state, dict):
                continue
            done = state.get("done", False)
            criteria = state.get("criteria", {})
            adv_rows.append({
                "player": player,
                "advancement_id": adv_id,
                "done": "YES" if done else "NO",
                "completed_criteria": len(criteria),
            })

    # Stable column order for the summary CSV.
    summary_cols = [
        "player",
        "play_minutes", "deaths", "jumps", "sleep_count",
        "walk_m", "sprint_m", "fly_m", "fall_m", "swim_m", "boat_m",
        "crouch_m", "walk_on_water_m", "walk_under_water_m",
        "damage_dealt_hearts", "damage_taken_hearts",
        "mob_kills_total", "killed_by_count",
        "blocks_mined_total", "items_used_total", "items_crafted_total",
        "items_picked_up_total", "items_dropped_total", "tools_broken",
        "time_since_rest_min", "time_since_death_min",
        "interact_furnace", "interact_crafting_table", "open_chest",
        "unique_blocks_mined", "unique_mobs_killed", "unique_items_used",
        "unique_items_crafted",
    ]
    with (OUT_DIR / "live_stats_summary.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=summary_cols)
        w.writeheader()
        for r in rows:
            # round floats to 1 decimal for readability
            row = {k: (f"{v:.1f}" if isinstance(v, float) else v) for k, v in r.items()}
            w.writerow({c: row.get(c, "") for c in summary_cols})

    with (OUT_DIR / "live_stats_detail.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["player", "category", "item", "count"])
        w.writeheader()
        w.writerows(detail_rows)

    with (OUT_DIR / "live_advancements.csv").open("w", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=["player", "advancement_id", "done", "completed_criteria"]
        )
        w.writeheader()
        w.writerows(adv_rows)

    return {
        "players": len(rows),
        "detail_rows": len(detail_rows),
        "adv_rows": len(adv_rows),
        "completed_advs": sum(1 for r in adv_rows if r["done"] == "YES"),
    }


def main():
    if not SNAP.exists():
        raise SystemExit(
            f"Snapshot dir not found: {SNAP}\n"
            f"This file is gitignored (lives under assets/). Auditors get the "
            f"snapshot out-of-band, same way they get assets/logs/."
        )
    stats = write_csvs()
    print(
        f"Wrote 3 snapshot CSVs to {OUT_DIR.relative_to(ROOT)}:\n"
        f"  live_stats_summary.csv ({stats['players']} players)\n"
        f"  live_stats_detail.csv  ({stats['detail_rows']} item rows)\n"
        f"  live_advancements.csv  ({stats['adv_rows']} entries, "
        f"{stats['completed_advs']} completed non-recipe)"
    )


if __name__ == "__main__":
    main()
