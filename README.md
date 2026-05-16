# The Hardcore Chronicles

An interactive Streamlit dashboard that tells the story of our hardcore Minecraft journey — every world attempted, every death, every reroll. Built from raw server logs.

![hero](https://img.shields.io/badge/49-worlds_attempted-FFC107) ![hero](https://img.shields.io/badge/30-ended_in_death-E63946) ![hero](https://img.shields.io/badge/19-rerolled-F4A261)

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Opens at `http://localhost:8501`.

## Deploy to Streamlit Community Cloud (free public URL)

1. Push this repo to a **public** GitHub repo.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app** → pick the repo, branch `main`, and `streamlit_app.py` as the entry point.
4. Click **Deploy**. You'll get a URL like `https://<your-app>.streamlit.app` to share.

No env vars or secrets needed — the CSVs ship with the repo.

## Data sources

All metrics are computed from CSVs in `data/`:

| File | What's in it |
| --- | --- |
| `summary.csv` | overall metrics (totals, failure rate, date range) |
| `worlds.csv` | one row per hardcore world; outcome + first-death info |
| `deaths.csv` | one row per death event; `is_first_in_world` flag |
| `death_messages.csv` | unique first-death phrasings + counts (Minecraft Wiki phrasing) |
| `players.csv` | per-player aggregates (first deaths, total deaths, PvP kills) |
| `pvp.csv` | killer → victim counts |

Regenerate from raw server logs by re-running the parsing script (lives outside this repo).

## Updating the data

Drop new CSVs into `data/` and the dashboard reflects them on next load. The `@st.cache_data` decorator caches per-session — restart the app or `streamlit rerun` to bust the cache.

## License

Personal project. Not affiliated with Mojang / Microsoft.
