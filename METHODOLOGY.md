# Methodology — How the Numbers Are Computed

**Audience:** external auditors verifying numbers/visuals before the client demo.

This document describes, in enough detail to reproduce every figure on the dashboard, how raw Minecraft server logs become the CSVs in `data/` and the charts in `Global_Stats.py` (page 1) plus `pages/2_Latest_World.py` (page 2). Skim Section 1, then work through Sections 2–6 to validate the pipeline, then run the spot-checks in Section 7.

---

## 1. Architecture in one diagram

```
   ┌────────────────────────────┐     ┌──────────────────────────────────┐
   │  Raw server logs (gz)      │     │  Live world snapshot             │
   │  assets/logs/vanilla/      │     │  assets/snapshots/live-world/    │
   │  assets/logs/forge/        │     │    players/{stats,advancements}/ │
   └────────────┬───────────────┘     └────────────────┬─────────────────┘
                │ parse_logs.py                        │ parse_snapshot.py
                ▼                                      ▼
   ┌────────────────────────────┐     ┌──────────────────────────────────┐
   │  Aggregate CSVs in data/   │     │  Snapshot CSVs in data/          │
   │  worlds, deaths,           │     │  live_stats_summary,             │
   │  death_messages, players,  │     │  live_stats_detail,              │
   │  pvp, summary,             │     │  live_advancements               │
   │  advancements              │     │                                  │
   └────────────┬───────────────┘     └────────────────┬─────────────────┘
                │  Global_Stats.py (page 1)            │  pages/2_Latest_World.py
                └─────────────┬────────────────────────┘
                              ▼
                  ┌────────────────────────┐
                  │  Browser dashboard     │
                  │  (multi-page)          │
                  └────────────────────────┘
```

Two sources of truth feed the dashboard:

- **Log-derived data** (covers all 44 hardcore worlds) — produced by `parse_logs.py` from the raw server logs. Drives page 1.
- **Snapshot-derived data** (covers only the currently-live world — 1 of 44) — produced by `parse_snapshot.py` from the server's `players/{stats,advancements}/*.json` NBT files. Drives page 2. Stats for the other 43 worlds were lost when the worlds were rerolled before any snapshot was taken.

Everything the UI shows is derivable from the CSVs in `data/`.

---

## 2. Inputs

Raw logs live under `assets/logs/`. They are **not** committed (they are personal/large); the `.gitignore` excludes `assets/`. Auditors should receive `assets/logs/` out of band and place it at the repo root.

```
assets/logs/vanilla/   # 14 files — server logs from the vanilla Minecraft era (2026-05-05 to 2026-05-07)
assets/logs/forge/     # 53 files — server logs after the Forge migration (2026-05-07 onward)
                       #   (45 main rotated logs + 1 latest.log + 5 debug-*.log.gz;
                       #    the debug-* family is *skipped* by the parser — see note below)
```

The `debug-N.log.gz` files mirror every INFO-level line from their matching main log (`YYYY-MM-DD-N.log.gz`). The parser deliberately ignores `debug-*` to avoid double-counting world creations, joins, advancements, and deaths. If you ever rename a real log to start with `debug-`, you'll lose its events — that's the trade-off for the simple filter rule.

Each log is a plain-text file (some `.log.gz`-compressed). Two timestamp formats appear:

| Era | Timestamp prefix on each line |
| --- | --- |
| Vanilla | `[HH:MM:SS]` — **no date**; the date is recovered from the **filename** (`YYYY-MM-DD-N.log.gz`). |
| Forge | `[DDMmmYYYY HH:MM:SS.mmm]` — full date in the line. |

Inside the line we look for **five** kinds of signal (case-sensitive):

| Signal | Example match | Used as |
| --- | --- | --- |
| World creation | `Worker-Main-1/INFO: ... creating new world` or `No existing world data, creating new world` | Boundary between successive worlds |
| Player joined | `axantroff joined the game` | Start of a play session |
| Player left | `axantroff left the game` | End of a play session |
| Death | `<player> was blown up by Creeper` (and 50+ other phrasings) | A death event |
| Advancement | `<player> has made the advancement [Diamonds!]` | A progression milestone |

The death-message verb list is taken verbatim from the official Minecraft Wiki (https://minecraft.fandom.com/wiki/Death_messages) and is sorted longest-phrase-first so the regex matches the most specific phrasing (e.g. `was burnt to a crisp whilst fighting` wins over `was burnt to a crisp`).

---

## 3. Parsing → events

`parse_logs.py:parse_events()` reads every file, line by line, and emits a stream of tuples `(timestamp, kind, who, payload, source_basename)` where `kind ∈ {W, J, A, D, L}`:

- **W** — world creation (no player attribution)
- **J** — player joined the game
- **A** — player earned an advancement (payload = the display name, without the brackets)
- **L** — player left the game
- **D** — player died (payload = full death-message phrase minus the leading player name, with trailing period stripped)

Players filtered to the three tracked accounts: `MurzichAI`, `axantroff`, `trofimova2002`. Events for other usernames are ignored.

**Edge case — vanilla logs crossing midnight:** the vanilla format has no date, so we infer it from the filename. If two consecutive lines show timestamps that go *backward* by more than 12 hours (e.g. 23:58 → 00:02), we bump the inferred date forward by one day. This handles the case where a single log file spans midnight without rolling over.

**Sort order:** events are sorted by `(timestamp, kind)` where kinds order as `W < J < A < D < L`. This guarantees that when a world-boundary and a death share the same second, the world boundary attaches first, so the death gets correctly counted in the *new* world. Advancements sort between J and D so a "joined the game" + "made the advancement" pair on the same second still attributes the join first. (See Section 7, spot-check #5.)

---

## 4. Events → worlds

`build_worlds()` walks the sorted event stream and partitions events into worlds. A world spans `[creation_ts, next_creation_ts)`. Worlds are 1-indexed in CSV output.

For each world we precompute:

- `window_end` — the end of the world's "lifetime" used for active-time math. Set to the first-death timestamp if anyone died, else the next world's creation timestamp. For the **last** world in the dataset (still ongoing), `window_end` is capped at the maximum event timestamp observed, never `now()` — this avoids inflating active time for unclosed sessions.

### 4.1 Hardcore cutoff

Hardcore mode was enabled at `2026-05-05 21:37` (when `server.properties` flipped `hardcore=false → hardcore=true` between server restarts; see commit history of the inline server we managed). **Only worlds created at or after this instant are part of the hardcore challenge.** Earlier worlds (and deaths within them) are excluded from every aggregate.

Concretely: there are **45 worlds** detected across all main logs, **44 of which are hardcore**. One pre-hardcore world (created 2026-05-05 21:24:22) contained one death (`MurzichAI was blown up by Creeper` at 21:49:18) — this is deliberately excluded because the run was not under hardcore rules.

---

## 5. Aggregations written to `data/`

`write_csvs()` consumes the hardcore worlds and produces seven CSVs.

### 5.1 `worlds.csv` — one row per hardcore world

| Column | Meaning |
| --- | --- |
| `world_num` | 1-indexed position among hardcore worlds (chronological). |
| `start_time` | World creation timestamp. |
| `outcome` | `died` (someone died at least once) or `skipped` (no death). |
| `first_death_at`, `first_death_player`, `first_death_message`, `first_death_category` | About the **first** death event in the world, sorted by timestamp. Empty for skipped. |
| `total_deaths` | All death events recorded in the world (including post-first; players go to spectator in hardcore but the log keeps recording them). |
| `wallclock_minutes` | Elapsed minutes from world creation to first death. **Includes server idle time** and is shown only for transparency. Empty for skipped. |
| `active_minutes` | Minutes during which **at least one** tracked player was logged in, computed by Section 5.2's algorithm. For skipped worlds this is from creation to next world creation. |
| `source_log` | Basename of the log file where the world-creation line was found. |

### 5.2 Active-time algorithm (the unique computation in this project)

The naive metric "first_death_at − start_time" is misleading because the server was often left running overnight or while we weren't playing. `active_minutes` instead measures the **union of intervals during which any tracked player was logged in**, clipped to the world's window:

```
1. Build per-player session list from J/L events.
   - Two J's for the same player with no L between them: close the earlier at the next J's timestamp.
   - L with no prior J: ignored.
   - J with no later L: closed at window_end.
2. Clip each (J_ts, L_ts) interval to [window_start, window_end].
3. Sort all (start, end) intervals across players and merge overlaps.
4. Sum the merged interval durations → active_minutes.
```

This means two players logged in simultaneously do not double-count. A 30-minute solo session counts as 30 minutes whether one or three players were online.

**Concrete example — World #15 (Dragon-fight run).**
The wall-clock duration is **1627 min** (~27 h). The active duration is **208 min** (~3.5 h). The 24-hour delta is server idle. The run ended with `MurzichAI was killed by Ender Dragon using magic` — the group reached the End but never beat the dragon.

### 5.3 `deaths.csv` — one row per death event

| Column | Meaning |
| --- | --- |
| `world_num` | Which hardcore world this death occurred in. |
| `timestamp` | Death timestamp. |
| `player` | One of `MurzichAI`, `axantroff`, `trofimova2002`. |
| `death_message` | Verb-phrase with the player name removed (e.g., `was blown up by Creeper`). |
| `full_message` | `<player> <death_message>`. |
| `is_first_in_world` | `YES` if this row is the chronologically earliest death of its world, else `NO`. |
| `category` | `Mob` / `Environment` / `PvP` / `Other`. Same logic as `worlds.first_death_category`. |
| `source_log` | Log file the death line was parsed from. |

Categorization rules (priority order):

1. **PvP** — message contains `by <PlayerName>` for one of the tracked players. (Surfaced in CSVs but filtered out of charts when the "Exclude PvP deaths" toggle is on, since these were goof-around moments, not the challenge.)
2. **Mob** — message contains any hostile-entity keyword (`creeper`, `zombie`, `enderman`, …).
3. **Environment** — message contains any environmental keyword (`fell`, `lava`, `stalagmite`, `lightning`, …).
4. **Other** — none of the above (very rare; flag for inspection).

The exact keyword lists are in `scripts/parse_logs.py` (`MOB_KEYWORDS`, `ENV_KEYWORDS`).

### 5.4 `death_messages.csv` — distinct phrasings, count restricted to first deaths

Every row represents one unique death-message string, with the number of **first-death-per-world** occurrences. Sum over this column equals the number of `died` worlds. This is the metric the chart "How Each Run Ended" visualizes.

### 5.5 `players.csv` — per-player counters

| Column | Meaning |
| --- | --- |
| `first_deaths` | Worlds where this player was the *first* to die. |
| `total_deaths` | Total death events for this player across all hardcore worlds. |
| `pvp_kills_on_others` | Count of `was * by <this player>` death-messages on others. |

### 5.6 `pvp.csv` — killer→victim pairs

One row per (killer, victim) pair with a non-zero count.

### 5.7 `summary.csv` — scalar overview

`metric,value` rows: `total_worlds_attempted`, `worlds_died`, `worlds_skipped`, `failure_rate_pct`, `total_deaths`, `unique_death_messages`, `total_active_minutes`, `total_active_hours`, `total_advancement_events`, `unique_advancements`, plus the `hardcore_from` cutoff for traceability.

### 5.8 `advancements.csv` — progression milestones (NEW)

One row per `<player> has made the advancement [<name>]` broadcast, attributed to the world that contained it. Only the official Mojang display names appear here (the bracketed string); recipe-unlock advancements never broadcast and are therefore absent.

| Column | Meaning |
| --- | --- |
| `world_num` | Hardcore world index this advancement belongs to. |
| `timestamp` | When the broadcast happened. |
| `player` | One of `MurzichAI`, `axantroff`, `trofimova2002`. |
| `advancement` | Display name verbatim (e.g. `Diamonds!`, `We Need to Go Deeper`, `A Terrible Fortress`). |
| `minutes_into_run` | Wall-clock minutes from this world's `start_time` to the advancement. **Not active-minutes** — interpret as "how far into the run, including idle time". |
| `source_log` | Log file the line was parsed from. |

Deduplication: if the same advancement broadcasts for the same player twice in the same world (rare — happens with some advancement criteria after relog), only the **earliest** is kept.

---

## 5b. Snapshot-derived CSVs (page 2 only)

`scripts/parse_snapshot.py` reads the currently-active Forge world's player files from `assets/snapshots/live-world/players/{stats,advancements}/*.json` and flattens them into three CSVs. **These cover only the single live world**, not the 44-world cumulative history.

### 5b.1 `live_stats_summary.csv` — per-player rollup

One row per player. ~30 columns of denormalized counters. Notable transformations:

- Distance counters in `minecraft:custom` (e.g. `minecraft:walk_one_cm`) are stored in centimeters — exported in **meters**.
- Time counters (`minecraft:play_time`, `time_since_rest`, `time_since_death`) are stored in game-ticks (20 ticks = 1 second) — exported in **minutes**.
- Damage counters (`damage_dealt`, `damage_taken`) are stored as integer tenths-of-hearts — exported in **hearts** (÷ 10).
- Totals like `blocks_mined_total` and `mob_kills_total` are sums over the corresponding `minecraft:*` category dict.

### 5b.2 `live_stats_detail.csv` — long-form item counters

One row per `(player, category, item)` triple covering all of `mined`, `killed`, `used`, `crafted`, `picked_up`, `dropped`, `broken`, and `killed_by`. The `minecraft:` namespace prefix is stripped from both `category` and `item` for readability. This is the source for the "Group Highlights" charts on page 2.

### 5b.3 `live_advancements.csv` — current advancement state

One row per non-recipe advancement entry in the live world. Columns: `player`, `advancement_id` (full Mojang ID like `minecraft:adventure/sleep_in_bed`), `done` (`YES`/`NO`), `completed_criteria` (number of sub-criteria the player has actually achieved). Recipe advancements (`minecraft:recipes/...`) are excluded — they fire on every craft and would drown the meaningful achievements.

Because the snapshot is a single point in time, `done == "NO"` rows represent advancements the player is *currently making progress on*, not advancements they have abandoned. After a reroll, this whole CSV resets.

---

## 6. Streamlit app

The dashboard is multi-page (Streamlit's `pages/` convention):

- **`Global_Stats.py`** — page 1 (sidebar label: "Global Stats"). Loads all log-derived CSVs (cached via `@st.cache_data`) and renders the all-44-worlds view.
- **`pages/2_Latest_World.py`** — page 2 ("The Latest World"). Loads the three snapshot CSVs and renders the live-world deep dive.

Neither page recomputes any source-of-truth metric — every chart reads directly from the CSV columns described above.

Page 1 unconditionally drops PvP-categorized worlds (`first_death_category == "PvP"`). They occurred during goofing-around between friends — not real hardcore attempts. The CSVs still contain them so auditors can see the underlying data, but every chart on page 1 hides them. The user-facing toggle was removed because the filter only affected ~1 in 10 worlds and clogged the top of the page.

One toggle remains at the top:

1. **Exclude worlds < 15 min active.** Filters out `worlds` rows where `active_minutes < 15`. **Default OFF** — the fresh page shows all 42 PvP-excluded attempts; the user can flip it on to drop the short rerolls. When on, the filtered set drives every hero metric, chart and the worlds table — including the Achievements section, which uses `worlds.world_num` as the join key against `advancements.csv`.

The Mob-vs-Environment donut additionally drops Other slices (it only ever shows Mob and Environment).

Page 2 has no filters — the snapshot is a single world's full state.

---

## 7. Auditor spot-checks

Run `python scripts/parse_logs.py` once to regenerate the CSVs from `assets/logs/`. The script prints a one-line counts summary; the rest of the checks operate on the resulting CSVs.

### 7.1 Top-level totals

Expected against the raw, unfiltered CSVs:

```
worlds:    44 hardcore
died:      29
skipped:   15
deaths:    51 total (29 first-deaths + 22 post-first-deaths)
active:    ~27 hours total
failure:   65.9% (worlds_died / worlds_total)
```

Verify in shell:

```bash
awk -F',' 'NR>1 {print $3}' data/worlds.csv | sort | uniq -c
# expected:  29 died / 15 skipped
awk -F',' 'NR>1 {n++} END {print n}' data/deaths.csv
# expected: 51
awk -F',' 'NR>1 && $6=="YES" {n++} END {print n}' data/deaths.csv
# expected: 29
```

### 7.2 Hardcore cutoff

```bash
awk -F',' 'NR>1 && $2 < "2026-05-05T21:37" {print $1, $2}' data/worlds.csv
# expected: (nothing — no pre-hardcore world should appear)
```

### 7.3 Active vs wall-clock for World #15 (the Dragon-fight run)

```bash
grep '^15,' data/worlds.csv
# Expected: world_num=15, outcome=died, wallclock_minutes≈1627, active_minutes≈208,
#           first_death_message="was killed by Ender Dragon using magic"
```

The 24-hour gap is overnight server idle. Cross-check by inspecting `assets/logs/forge/2026-05-1*.log.gz` (skip the `debug-*` mirrors) for `joined the game` / `left the game` events around the world's start and the `was killed by Ender Dragon using magic` line.

### 7.4 First-death sum equals failed worlds

```bash
.venv/bin/python -c "
import pandas as pd
d = pd.read_csv('data/death_messages.csv')
print(d['count_first_deaths_only'].sum())  # expected: 29
"
```

### 7.5 World-boundary tie-breaking

Search for any death event with the same timestamp as a world-creation event:

```bash
.venv/bin/python -c "
import pandas as pd
w = pd.read_csv('data/worlds.csv')
# parse_dates can't be used here — first_death_at is empty for skipped worlds
# and would leave the column as object dtype, breaking the .dt accessor below.
w['start_time']     = pd.to_datetime(w['start_time'],     errors='coerce')
w['first_death_at'] = pd.to_datetime(w['first_death_at'], errors='coerce')
both = w.dropna(subset=['first_death_at'])
collisions = both[both.first_death_at.dt.floor('s') == both.start_time.dt.floor('s')]
print(collisions.shape[0])  # expected: 0 — deaths and world creations should never share a second
"
```

### 7.6 Category mutual exclusivity

```bash
awk -F',' 'NR>1 {print $7}' data/worlds.csv | sort | uniq -c
# expected: ('', Mob, Environment, PvP) only; no 'Other'
```

If any rows fall into `Other`, the death-verb regex matched a phrasing that wasn't covered by `MOB_KEYWORDS` or `ENV_KEYWORDS`. Add the missing keyword to `parse_logs.py` and regenerate.

### 7.7 Advancements sanity

```bash
.venv/bin/python -c "
import csv
rows = list(csv.DictReader(open('data/advancements.csv')))
print(f'total events: {len(rows)}')             # expected: 500
worlds = set(r['world_num'] for r in rows)
print(f'worlds with any advancement: {len(worlds)}')  # expected: <= 44
names = set(r['advancement'] for r in rows)
print(f'unique advancements: {len(names)}')     # expected: 29
"
```

If `total events` shifts by more than ~5, suspect either a parser regex change or a duplicate-suppression bug in `write_csvs` (the seen-set guard against repeat broadcasts per (world, player, advancement)).

### 7.8 Snapshot consistency

```bash
.venv/bin/python -c "
import csv
rows = list(csv.DictReader(open('data/live_stats_summary.csv')))
print(f'players in snapshot: {len(rows)}')      # expected: 3
print(f'total play minutes:', sum(float(r['play_minutes']) for r in rows))
# Expected: ~340 min combined across 3 players (148 + 100 + 97).
# This is per-player play_time, NOT the same metric as active_minutes
# from worlds.csv — those measure different things.
"
```

### 7.9 Streamlit sanity

Start the app and confirm hero numbers change when toggles flip:

```bash
.venv/bin/streamlit run Global_Stats.py
```

With the `<15 min active` toggle **OFF** (default — PvP-categorized worlds are *always* excluded; no UI toggle for that anymore — see §6): "Worlds Attempted" reads **42**, "Ended in Death" **27**, "Skipped" **15**, "Total Active Play" ~**25.9h**.

With the `<15 min active` toggle **ON**: drops short rerolls; reads **16 / 16 / 0 / ~24h** (all surviving worlds are `died`; no skipped run lasted 15 active minutes).

Raw CSVs (no filters at all) hold the full ground-truth: **44 / 29 / 15 / ~27h** — these match §7.1.

Navigate to "Latest World" in the sidebar — it should show three player cards (one per tracked account) and the six "Group Highlights" bar charts (mined / killed / used / crafted / picked up / dropped).

---

## 8. Known caveats

- **Vanilla midnight crossings** depend on the heuristic in `parse_ts`. If you ever import logs that *intentionally* go backward in time (clock drift, NTP correction), this heuristic could mis-attribute by a day. Manual review of the inferred dates was done for the 2026-05-05 to 2026-05-07 vanilla window; no anomalies remain.
- **Death attribution for spectators in hardcore.** Vanilla hardcore puts dead players into spectator mode but still logs subsequent "deaths" if e.g. they fall through a portal as spectator (rare). Such follow-up entries are included in `total_deaths` but never in `first_deaths`; only first-death stats drive the failure metric.
- **PvP attribution.** Categorization keys on the literal substring `by <PlayerName>`. If a mob's display-name ever matched a tracked player's name, it would mis-categorize — but our three players' names don't collide with any vanilla entity name.
- **Active-minutes precision.** Session boundaries are resolved to 1-second granularity (the Minecraft log timestamp resolution). Sessions shorter than 1 second are rounded down; cumulative drift is bounded by `O(sessions × 0.5s)`.
- **One pre-hardcore death is excluded by design** (Section 4.1). If you see "51 deaths total" but the raw log inventory suggests 52, that's the reason.
- **`debug-*.log.gz` files are deliberately skipped** (see §2). Each one mirrors INFO lines from its main-log sibling; including both would double-count world creations, joins, advancements, and deaths. Diagnostic regeneration *with* debug logs reports 49 / 20 / 53 instead of 44 / 15 / 51 — those are the inflated numbers, not the real ones.
- **Snapshot coverage is 1 world out of 44.** The other 43 worlds were rerolled before any snapshot of `players/{stats,advancements}/` was preserved. Page 2 metrics are therefore *not* representative of the whole journey — they describe just one current attempt. The disclaimer is shown on page 2 itself.
- **`minutes_into_run` in `advancements.csv` is wall-clock**, not active-minutes. We chose wall-clock for the advancement-time stats because (a) most advancements that matter for "time-to-X" charts (iron, diamond, Nether) trigger in tightly-clustered sessions where idle time isn't material, and (b) re-running the active-time algorithm per-advancement would cost ~10× more parsing for marginal accuracy gain. If a run's wall-clock and active times diverge dramatically (e.g. the Dragon-fight world #15), interpret with care.
- **`fly_one_cm` is not elytra-specific.** Minecraft increments this counter while any in-air movement happens — jumping, falling, gliding. In a vanilla hardcore game where nobody has reached the End, this counter is almost entirely jump/fall time. Page 2 labels it "Air Time" for that reason.

---

## 9. Reproducing from scratch

```bash
git clone <repo>
cd hardcore-chronicles
# obtain assets/ from the source out-of-band, then:
ls assets/logs/vanilla/ | wc -l                       # expect: 14
ls assets/logs/forge/   | wc -l                       # expect: 51
ls assets/snapshots/live-world/players/stats/ | wc -l # expect: 3

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/parse_logs.py        # regenerates data/{worlds,deaths,...,advancements}.csv
python scripts/parse_snapshot.py    # regenerates data/live_stats_*.csv + live_advancements.csv
streamlit run Global_Stats.py       # opens at localhost:8501 (use sidebar to switch pages)
```

If the regenerated CSVs are byte-different from what's committed, that's a regression. Read the diff carefully — both parsers are intentionally deterministic given the same input files.
