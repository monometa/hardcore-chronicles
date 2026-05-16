# Backlog

Things to do **after** the auditor review lands — not blockers, not regressions, just polish and feature ideas worth tracking. For framing rules (what *not* to do), see `task.md §4`. For why a stat is interesting given how we play, see `PLAYSTYLE.md`.

---

## Page 2 (Latest World) — fits PLAYSTYLE.md directly

### 1. Head-to-Head on core resources
Side-by-side per-player bar charts on the counters that "settle arguments" (per PLAYSTYLE.md §2 *Head-to-Head*). Candidates — open list, add more as they feel meaningful:
- Wood mined (oak / spruce / birch — broken down or summed)
- Stone / cobblestone mined
- Coal / iron / diamonds mined
- Mobs killed
- **Damage dealt and damage taken** — already in Tale-of-the-Tape, but a side-by-side bar would land narratively
- Food eaten (who's burning through all the bread?)

Data: already in `data/live_stats_detail.csv`. No parser change needed.

### 2. Role Signatures panel
Three cards, one per player, surfacing each player's *signature* counters (per PLAYSTYLE.md §1):
- **trofimova2002** — `open_chest`, `used:*_sapling` (sum across sapling types), `interact_crafting_table`, items dropped (= sorted into chests).
- **MurzichAI** — villager trades, XP levels gained, items enchanted, emeralds earned. *Needs parser extension (#4) — these counters aren't in `live_stats_summary.csv` yet.*
- **axantroff** — deepest Y mined, time in Nether, time in End. *Hard from current snapshot — needs NBT parsing or session-time reconstruction from logs.*

### 3. "Tools broken" chart
`tools_broken` is already in `live_stats_summary.csv` but not surfaced as its own chart. Cheap win — a single bar of "tools each player wore through" is a fun side-stat that flatters trofimova (axantroff data: 10 tools broken).

---

## Snapshot pipeline

### 4. Extend `parse_snapshot.py` to pull deeper counters
For Role Signatures (#2), we need to surface these `minecraft:custom` keys: `traded_with_villager`, `xp_gained`, `enchant_item`. All already in the per-player JSON, just not in our summary CSV.

### 5. Pre-reroll snapshot hook
The reason we have data for only 1 world (out of 44) is that earlier worlds were rerolled without ever capturing `players/{stats,advancements,data}/`. A small script (cron / pre-reroll hook / manual `make snapshot`) that copies the live world's player files to `assets/snapshots/world-<N>-<timestamp>/` before deletion would preserve future runs and let page 2 evolve into a multi-world view.

---

## Visual / theme polish (from `task.md §8`)

### 6. Custom Minecraft visuals
- Pixel font for titles (e.g., Press Start 2P via Google Fonts) — readability trade-off
- Subtle cobblestone CSS background texture
- Inline per-mob PNG icons in death-message labels (currently emoji-only)

---

## Quality / reproducibility (from pre-audit pass)

### 7. Pin `requirements.txt` exactly
Current bounds use `>=` minimums. For strict auditor reproducibility, switch to exact pins (`streamlit==1.50.0` etc.). Trade-off: more friction if someone is on a newer Streamlit release.

### 8. Migrate off deprecated `use_container_width`
8 deprecation warnings during page 1 render. Streamlit will eventually remove the parameter; the replacement (`width="stretch"`) isn't yet a clean fit on `st.plotly_chart` (falls through `**kwargs` and triggers a *different* deprecation). Migrate once Streamlit lands the proper path.

### 9. Smoke-test script
A `scripts/verify.sh` (or `make verify`) that runs both parsers, AppTests both pages, and confirms ground-truth numbers. Saves the next contributor (or auditor) the manual sequence in METHODOLOGY §7.

---

## Deployment (from `task.md §8`)

### 10. Streamlit Community Cloud deploy
- Push repo to a public GitHub repo
- Configure at `share.streamlit.io`, entry-point `Global_Stats.py`, branch `main`
- Smoke-test both pages in the cloud environment before sharing the URL with friends

---

*Update this file as items get picked up, dropped, or new ones land. Move completed items into git commit messages rather than leaving a "done" pile here.*
