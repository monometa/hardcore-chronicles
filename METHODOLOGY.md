# Methodology — How the Numbers Are Computed

**Audience:** external auditors verifying numbers/visuals before the client demo.

This document describes, in enough detail to reproduce every figure on the dashboard, how raw Minecraft server logs become the CSVs in `data/` and the charts in `streamlit_app.py`. Skim Section 1, then work through Sections 2–6 to validate the pipeline, then run the spot-checks in Section 7.

---

## 1. Architecture in one diagram

```
              ┌────────────────────────┐
              │  Raw server logs (gz)  │
              │  assets/logs/vanilla/  │
              │  assets/logs/forge/    │
              └───────────┬────────────┘
                          │  python scripts/parse_logs.py
                          ▼
              ┌────────────────────────┐
              │  CSV facts in data/    │
              │  worlds, deaths,       │
              │  death_messages,       │
              │  players, pvp, summary │
              └───────────┬────────────┘
                          │  streamlit run streamlit_app.py
                          ▼
              ┌────────────────────────┐
              │  Browser dashboard     │
              └────────────────────────┘
```

There is one source of truth (the gzipped logs in `assets/logs/`) and one transformation step (`parse_logs.py`). Everything the UI shows is derivable from the CSVs.

---

## 2. Inputs

Raw logs live under `assets/logs/`. They are **not** committed (they are personal/large); the `.gitignore` excludes `assets/`. Auditors should receive `assets/logs/` out of band and place it at the repo root.

```
assets/logs/vanilla/   # 14 files — server logs from the vanilla Minecraft era (2026-05-05 to 2026-05-07)
assets/logs/forge/     # 51 files — server logs after the Forge migration (2026-05-07 onward)
```

Each log is a plain-text file (some `.log.gz`-compressed). Two timestamp formats appear:

| Era | Timestamp prefix on each line |
| --- | --- |
| Vanilla | `[HH:MM:SS]` — **no date**; the date is recovered from the **filename** (`YYYY-MM-DD-N.log.gz`). |
| Forge | `[DDMmmYYYY HH:MM:SS.mmm]` — full date in the line. |

Inside the line we look for **four** kinds of signal (case-sensitive):

| Signal | Example match | Used as |
| --- | --- | --- |
| World creation | `Worker-Main-1/INFO: ... creating new world` or `No existing world data, creating new world` | Boundary between successive worlds |
| Player joined | `axantroff joined the game` | Start of a play session |
| Player left | `axantroff left the game` | End of a play session |
| Death | `<player> was blown up by Creeper` (and 50+ other phrasings) | A death event |

The death-message verb list is taken verbatim from the official Minecraft Wiki (https://minecraft.fandom.com/wiki/Death_messages) and is sorted longest-phrase-first so the regex matches the most specific phrasing (e.g. `was burnt to a crisp whilst fighting` wins over `was burnt to a crisp`).

---

## 3. Parsing → events

`parse_logs.py:parse_events()` reads every file, line by line, and emits a stream of tuples `(timestamp, kind, who, payload, source_basename)` where `kind ∈ {W, J, D, L}`:

- **W** — world creation (no player attribution)
- **J** — player joined the game
- **L** — player left the game
- **D** — player died (payload = full death-message phrase minus the leading player name, with trailing period stripped)

Players filtered to the three tracked accounts: `MurzichAI`, `axantroff`, `trofimova2002`. Events for other usernames are ignored.

**Edge case — vanilla logs crossing midnight:** the vanilla format has no date, so we infer it from the filename. If two consecutive lines show timestamps that go *backward* by more than 12 hours (e.g. 23:58 → 00:02), we bump the inferred date forward by one day. This handles the case where a single log file spans midnight without rolling over.

**Sort order:** events are sorted by `(timestamp, kind)` where kinds order as `W < J < D < L`. This guarantees that when a world-boundary and a death share the same second, the world boundary attaches first, so the death gets correctly counted in the *new* world. (See Section 7, spot-check #5.)

---

## 4. Events → worlds

`build_worlds()` walks the sorted event stream and partitions events into worlds. A world spans `[creation_ts, next_creation_ts)`. Worlds are 1-indexed in CSV output.

For each world we precompute:

- `window_end` — the end of the world's "lifetime" used for active-time math. Set to the first-death timestamp if anyone died, else the next world's creation timestamp. For the **last** world in the dataset (still ongoing), `window_end` is capped at the maximum event timestamp observed, never `now()` — this avoids inflating active time for unclosed sessions.

### 4.1 Hardcore cutoff

Hardcore mode was enabled at `2026-05-05 21:37` (when `server.properties` flipped `hardcore=false → hardcore=true` between server restarts; see commit history of the inline server we managed). **Only worlds created at or after this instant are part of the hardcore challenge.** Earlier worlds (and deaths within them) are excluded from every aggregate.

Concretely: there are **50 worlds** detected across all logs, **49 of which are hardcore**. One pre-hardcore world (created 2026-05-05 21:24:22) contained one death (`MurzichAI was blown up by Creeper` at 21:49:18) — this is deliberately excluded because the run was not under hardcore rules.

---

## 5. Aggregations written to `data/`

`write_csvs()` consumes the hardcore worlds and produces six CSVs.

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

**Concrete example — World #16 (Dragon kill).**
The wall-clock duration is **1627 min** (~27 h). The active duration is **208 min** (~3.5 h). The 24-hour delta is server idle.

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

`metric,value` rows: `total_worlds_attempted`, `worlds_died`, `worlds_skipped`, `failure_rate_pct`, `total_deaths`, `unique_death_messages`, `total_active_minutes`, `total_active_hours`, plus the `hardcore_from` cutoff for traceability.

---

## 6. Streamlit app

`streamlit_app.py` loads the six CSVs (cached via `@st.cache_data`) and renders the dashboard. It performs no recomputation of the source-of-truth metrics — every chart reads directly from the CSV columns described above. The two toggles at the top apply **after** load:

1. **Exclude worlds < 15 min active.** Filters out `worlds` rows where `active_minutes < 15`. Default ON. The filtered set drives every chart and the worlds table.
2. **Exclude PvP deaths.** Filters out `worlds` rows where `first_death_category == "PvP"`. Default ON. Same propagation.

The Mob-vs-Environment donut additionally drops PvP/Other slices (it only ever shows Mob and Environment). The "How Each Run Ended" bar chart keeps every category, color-coded; PvP rows simply disappear when the toggle filters them out.

---

## 7. Auditor spot-checks

Run `python scripts/parse_logs.py` once to regenerate the CSVs from `assets/logs/`. The script prints a one-line counts summary; the rest of the checks operate on the resulting CSVs.

### 7.1 Top-level totals

Expected when both filter-toggles are **OFF**:

```
worlds:    49 hardcore
died:      29
skipped:   20
deaths:    53 total (29 first-deaths + 24 post-first-deaths)
active:    ~27 hours total
```

Verify in shell:

```bash
awk -F',' 'NR>1 {print $3}' data/worlds.csv | sort | uniq -c
# expected:  29 died / 20 skipped
awk -F',' 'NR>1 {n++} END {print n}' data/deaths.csv
# expected: 53
awk -F',' 'NR>1 && $6=="YES" {n++} END {print n}' data/deaths.csv
# expected: 29
```

### 7.2 Hardcore cutoff

```bash
awk -F',' 'NR>1 && $2 < "2026-05-05T21:37" {print $1, $2}' data/worlds.csv
# expected: (nothing — no pre-hardcore world should appear)
```

### 7.3 Active vs wall-clock for World #16 (the Dragon kill)

```bash
grep '^16,' data/worlds.csv
# Expected columns: world_num=16, outcome=died, wallclock_minutes≈1627, active_minutes≈208
```

The 24-hour gap is overnight server idle. Cross-check by inspecting `assets/logs/forge/2026-05-1*.gz` for `joined the game` / `left the game` events around the world's start and `was killed by Ender Dragon` line.

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
w = pd.read_csv('data/worlds.csv', parse_dates=['start_time','first_death_at'])
collisions = w[w.first_death_at.dt.floor('s') == w.start_time.dt.floor('s')]
print(collisions.shape[0])  # expected: 0 — deaths and world creations should never share a second
"
```

### 7.6 Category mutual exclusivity

```bash
awk -F',' 'NR>1 {print $7}' data/worlds.csv | sort | uniq -c
# expected: ('', Mob, Environment, PvP) only; no 'Other'
```

If any rows fall into `Other`, the death-verb regex matched a phrasing that wasn't covered by `MOB_KEYWORDS` or `ENV_KEYWORDS`. Add the missing keyword to `parse_logs.py` and regenerate.

### 7.7 Streamlit sanity

Start the app and confirm hero numbers change when toggles flip:

```bash
.venv/bin/streamlit run streamlit_app.py
```

With both toggles **ON** (default): "Worlds Attempted" should drop below 49 (rerolls + PvP filtered). With both **OFF**: should return to 49 / 29 / 20 / ~27h.

---

## 8. Known caveats

- **Vanilla midnight crossings** depend on the heuristic in `parse_ts`. If you ever import logs that *intentionally* go backward in time (clock drift, NTP correction), this heuristic could mis-attribute by a day. Manual review of the inferred dates was done for the 2026-05-05 to 2026-05-07 vanilla window; no anomalies remain.
- **Death attribution for spectators in hardcore.** Vanilla hardcore puts dead players into spectator mode but still logs subsequent "deaths" if e.g. they fall through a portal as spectator (rare). Such follow-up entries are included in `total_deaths` but never in `first_deaths`; only first-death stats drive the failure metric.
- **PvP attribution.** Categorization keys on the literal substring `by <PlayerName>`. If a mob's display-name ever matched a tracked player's name, it would mis-categorize — but our three players' names don't collide with any vanilla entity name.
- **Active-minutes precision.** Session boundaries are resolved to 1-second granularity (the Minecraft log timestamp resolution). Sessions shorter than 1 second are rounded down; cumulative drift is bounded by `O(sessions × 0.5s)`.
- **One pre-hardcore death is excluded by design** (Section 4.1). If you see "53 deaths total" but the unfiltered chart shows 54, that's the reason.

---

## 9. Reproducing from scratch

```bash
git clone <repo>
cd hardcore-chronicles
# obtain assets/ from the source out-of-band, then:
ls assets/logs/vanilla/ | wc -l   # expect: 14
ls assets/logs/forge/   | wc -l   # expect: 51

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/parse_logs.py      # regenerates data/*.csv
streamlit run streamlit_app.py    # opens at localhost:8501
```

If the regenerated CSVs are byte-different from what's committed, that's a regression. Read the diff carefully — the parser is intentionally deterministic given the same input logs.
