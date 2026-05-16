# The Hardcore Chronicles

An interactive Streamlit dashboard that tells the story of our hardcore Minecraft journey — every world attempted, every death, every reroll. Built from raw server logs.

![hero](https://img.shields.io/badge/44-worlds_attempted-FFC107) ![hero](https://img.shields.io/badge/29-ended_in_death-E63946) ![hero](https://img.shields.io/badge/15-rerolled-F4A261)


## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run Global_Stats.py
```

Opens at `http://localhost:8501`.

## Deploy to Streamlit Community Cloud (free public URL)

1. Push this repo to a **public** GitHub repo.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app** → pick the repo, branch `main`, and `Global_Stats.py` as the entry point.
4. Click **Deploy**. You'll get a URL like `https://<your-app>.streamlit.app` to share.

No env vars or secrets needed — the CSVs ship with the repo.

## Pages

The app is multi-page (use the sidebar to switch):

1. **Global Stats** (`Global_Stats.py`) — all 44 worlds: death causes, run durations, achievement progression, per-player tally, daily attempt density.
2. **The Latest World** (`pages/2_Latest_World.py`) — deep dive into the currently-active world: per-player stat cards, movement breakdown, "what we did most" bars (mined / killed / crafted / used), advancement state.

## Data sources

All metrics are computed from CSVs in `data/`:

| File | Drives | What's in it |
| --- | --- | --- |
| `summary.csv` | page 1 | overall metrics (totals, failure rate, total active hours, advancements, hardcore cutoff) |
| `worlds.csv` | page 1 | one row per hardcore world; outcome + first-death + active/wallclock minutes |
| `deaths.csv` | page 1 | one row per death event; `is_first_in_world` flag, category |
| `death_messages.csv` | page 1 | unique first-death phrasings + counts (Minecraft Wiki phrasing) |
| `players.csv` | page 1 | per-player aggregates (first deaths, total deaths, PvP kills) |
| `pvp.csv` | page 1 | killer → victim counts |
| `advancements.csv` | page 1 | one row per advancement broadcast, attributed to its world |
| `live_stats_summary.csv` | page 2 | per-player counters from the live world snapshot |
| `live_stats_detail.csv` | page 2 | long-form item counts (mined / killed / crafted / …) per player |
| `live_advancements.csv` | page 2 | per-player advancement state in the live world |

Regenerate them from the raw inputs:

```bash
python scripts/parse_logs.py        # logs → worlds/deaths/.../advancements CSVs
python scripts/parse_snapshot.py    # live-world snapshot → live_stats_* CSVs
```

Raw inputs (gzipped logs + the live-world snapshot) live under `assets/`. **The `assets/` directory is gitignored** — auditors must obtain it out-of-band and drop it at the repo root before running the parsers.

## For auditors

[`METHODOLOGY.md`](METHODOLOGY.md) is the source-of-truth for *how every number is computed*, with explicit spot-checks. Read it before validating the dashboard. The pipeline has one transformation step (`scripts/parse_logs.py`); everything in `data/` is derivable from `assets/logs/` and that script alone.

## Updating the data

Drop new CSVs into `data/` and the dashboard reflects them on next load. The `@st.cache_data` decorator caches per-session — restart the app or `streamlit rerun` to bust the cache.

## License

Personal project. Not affiliated with Mojang / Microsoft.
