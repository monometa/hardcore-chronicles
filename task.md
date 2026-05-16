# Hardcore Chronicles — Task Brief

Consolidated context for anyone (Claude, auditor, or new contributor) picking this project up. Everything in this file is **not duplicated** in `README.md` or `METHODOLOGY.md` — those describe *what the code does*; this file describes *why the project exists, who it is for, and which decisions are load-bearing*.

---

## 1. Background

`axantroff` and two friends (`MurzichAI`, `trofimova2002`) play Minecraft hardcore together. Over ~11 days (May 5 – May 16, 2026) they ran **49 hardcore attempts**, all of which ended in death or were rerolled. No challenge was ever beaten. This dashboard tells the story of that journey.

The Minecraft server itself is hosted on axantroff's Mac, exposed to friends via a playit.gg tunnel (the agent runs in Docker). The server is Forge 64.0.8 / MC 26.1.2 with three server-side mods: **FallingTree**, **collective** (FallingTree dependency), and **villagespawnpoint**. Hardcore mode was enabled by editing `server.properties` on **2026-05-05 21:37**; everything before that timestamp is excluded from analysis.

The server's raw logs live on the same machine. They are the only input to this project.

---

## 2. Goals & audience

1. **Share with friends.** axantroff wants a public URL to send to MurzichAI and trofimova2002 so they can browse the history together. Targeted host: Streamlit Community Cloud (free, GitHub-connected) — not yet deployed; user will push to GitHub and configure it themselves.
2. **Pre-demo audit.** Two external auditors will validate the numbers and viz quality before a client demo. They follow `METHODOLOGY.md` step-by-step and have access to `assets/logs/` out of band. They must be able to re-run `scripts/parse_logs.py` and reproduce every figure on the dashboard.
3. **Tone matters.** The dashboard is meant to celebrate the journey, not embarrass the player who ruined the most runs. Framing rules in section 4.

---

## 3. Players

| Player | Role | Offline-mode UUID |
| --- | --- | --- |
| `axantroff` | Project owner / commissioner of this dashboard | `b640b54b-74f4-332d-a6ca-62f3f8849bfd` |
| `MurzichAI` | Friend | `9f7deb4a-782c-3f6b-8366-625193e5854b` |
| `trofimova2002` | Friend | `0667e348-1378-36ef-a6c1-0132de3090b4` |

All three use TLauncher (offline mode). UUIDs are computed deterministically via MD5 of `OfflinePlayer:<name>` with version-3 / variant bits set; the dashboard does not depend on these UUIDs — they're only relevant if you inspect raw `world/players/stats/*.json` files.

---

## 4. Hard constraints (do not violate)

These come directly from axantroff's feedback during development and are non-negotiable. Anything that breaks one of them is a regression.

1. **Never use the word "Survived."** The group never beat hardcore. Worlds without a death are `skipped` or `re-created`, *not* survived.
2. **Never frame the dashboard as a leaderboard / competition.** No medals, no "challenge failed by," no podium positioning. The first-death-per-player view is shown low on the page under a neutral header ("Per Player") and respects the same filters as the rest.
3. **`active_minutes` is the canonical "how long did the run last" metric.** Wall-clock time inflates the longest run from 3.5 h (real play) to 27 h (server idled overnight). Both are stored in `worlds.csv` for transparency; charts use `active_minutes`.
4. **Filter `<15 min active` and PvP deaths by default.** Both are surfaced as toggles, both default ON. The reasoning: ultra-short runs are rerolls / messing around, and PvP deaths (one of us killing another) were goofing around, not the challenge.
5. **Hardcore cutoff is `2026-05-05 21:37`.** Worlds created before this point — and any death within them — are excluded. The one pre-hardcore Creeper death (a real event) is deliberately dropped; this is documented in METHODOLOGY.md §4.1.
6. **First-death is what matters.** Post-first deaths are recorded but never used to drive failure metrics (a hardcore world is "over" the moment someone dies; subsequent deaths are spectator goofing).
7. **Death messages must use the official Minecraft Wiki phrasing.** Source: https://minecraft.fandom.com/wiki/Death_messages. The verb list in `scripts/parse_logs.py` is taken verbatim from there.
8. **"Mob vs Environment" is a meaningful breakdown; "PvP" is not a real category.** The donut shows only Mob and Environment slices, even when PvP deaths exist in the data.
9. **Global desc sort on "How Each Run Ended."** Plotly's default behavior groups bars by color/category — that ordering is wrong. The y-axis category order is locked to the count-desc-sorted label list.

---

## 5. Style & tone preferences

- **Visual identity is Minecraft.** Colors come from in-game blocks: gold ingot (`#FFAA00`) for accents/titles, redstone (`#DC2626`) for hostile mobs, lava (`#FF8C1A`) for environment, diamond (`#3DD5F3`) for player accent, grass-block top (`#7CB342`) for positive/neutral. Background is obsidian-dark (`#1B1D24`); surfaces are stone (`#2A2D36`). **Do not use muted dark-green palettes** — that was an early version and felt like a generic ops dashboard.
- **Hero numbers are large and gold with a subtle text-shadow glow.** Cards have stone-colored borders. This is the "inventory slot" feeling.
- **Typography is monospace** (rendered as DejaVu Sans Mono or system mono). Bold titles, generous letter-spacing.
- **Emojis are OK in Streamlit** (it renders Apple Color Emoji or fallback). They were **not** OK in matplotlib (the v1 prototype used DejaVu Sans Mono which has no emoji glyphs — they came out as boxes).
- **Fun facts must be unique** — never duplicate what's already shown above. "% of deaths by stalagmite" is a fun fact; "X total deaths" is a duplicate of a hero card. The current "Key Insights" panel computes share of top cause, top-3 cumulative share, count of once-only causes, mob-vs-env split, deadliest specific enemy, and mean active life.

---

## 6. Decision history (why the project looks like it does)

The dashboard went through three eras. Each transition was driven by axantroff's feedback.

### Era 1 — single matplotlib PNG
Started as a static infographic generated by an inline Python script. Early flaws:
- Death-message y-axis labels got cut off (long phrasings like `<player> was burned to a crisp while fighting Blaze`).
- Emoji icons rendered as missing-glyph boxes.
- Outcomes panel said "Survived" — incorrect framing.
- "Cause subtitle" mentioned the Minecraft Wiki — implementation detail leaking into UI.
- Layout cramped pie + bars together.

axantroff's rating: 5/10 → after layout fixes 8/10. Still not 9.

### Era 2 — conceptual switch to Streamlit
axantroff explicitly stopped the matplotlib track and asked for a **Streamlit app in a new git repo with CSV data sources**, deployable to a public URL. This is the current architecture:
- `streamlit_app.py` + `data/*.csv` + `scripts/parse_logs.py`
- Local venv at `.venv/`
- Tested locally at `http://localhost:8501`
- Deploy target: Streamlit Community Cloud (free, GitHub-connected)

### Era 3 — accuracy & polish iterations
The user's pickier passes:
- Initial palette was muted dark-green; switched to Minecraft block colors (section 5).
- Discovered wall-clock duration was being inflated by overnight server idle (e.g., the "Dragon kill" run looked like 1627 min but was actually 208 min of real play). Added `active_minutes` computed from `joined the game` / `left the game` events.
- Added two filter toggles (15-min minimum, PvP exclusion); both default ON.
- Removed "Fun Facts" because they duplicated hero metrics; replaced with "Key Insights" containing genuinely unique stats.
- Re-added a "Per Player" tally near the bottom of the page with neutral framing (no medals).
- Forced global desc sort on the death-messages bar chart (plotly was grouping by category).
- Caught and fixed two parser bugs along the way (a 2030-window-end inflation, and an inline pre-hardcore Creeper death that had been mis-attributed).

### Era 4 — auditor handoff
The most recent additions:
- `METHODOLOGY.md` — full audit guide with 7 numbered spot-checks.
- `scripts/parse_logs.py` — standalone, idempotent CSV regenerator.
- `assets/logs/` — raw logs bundled locally for auditors (gitignored, transferred out of band).

---

## 7. Ground-truth numbers (current state)

With both filter toggles **OFF** (raw view):

| Metric | Value |
| --- | --- |
| Total hardcore worlds | 49 |
| Died (run ended in death) | 29 |
| Skipped (no death — rerolled) | 20 |
| Total death events | 53 (29 first-deaths + 24 post-first) |
| Unique death-message phrasings | 19 |
| Total active play | ~27 hours |

Per-player first-death counts (default filters OFF): MurzichAI dominates the count; exact numbers in `data/players.csv`. Do not lead with this; respect framing rule #2.

If the regenerated CSVs differ from these numbers, that's a regression — read METHODOLOGY.md §7 spot-checks before changing anything.

---

## 8. Open items / next steps

1. **Deploy to Streamlit Community Cloud.** axantroff handles this:
   - Push repo to a public GitHub repo (`gh repo create hardcore-chronicles --public --source=. --remote=origin --push`)
   - Connect at https://share.streamlit.io, point at `streamlit_app.py`, `main` branch
   - Expected URL pattern: `https://<user>-hardcore-chronicles.streamlit.app`
2. **Custom Minecraft visuals.** Was discussed but not done:
   - Pixel font for titles (e.g., Press Start 2P via Google Fonts) — possible but readability tradeoff
   - Subtle cobblestone CSS background texture — could help vibe
   - Inline per-mob PNG icons in death-message labels — bigger lift; currently we use emojis
3. **Audit pass.** Two external auditors will work through METHODOLOGY.md before the client demo. They have not yet started. Any number reported in the dashboard must round-trip through `scripts/parse_logs.py` from the bundled `assets/logs/`.

---

## 9. Continuity for the next session

If a future Claude (or human) opens this project cold, here's the minimum to get oriented:

**Files in priority order:**

1. `task.md` — this file. Read first.
2. `METHODOLOGY.md` — how every number is computed; auditor handoff.
3. `README.md` — install + deploy.
4. `streamlit_app.py` — the dashboard.
5. `scripts/parse_logs.py` — the parser.
6. `data/*.csv` — derived facts.

**Local operations:**

```bash
cd ~/hardcore-chronicles

# regenerate CSVs from raw logs (assets/ must exist)
.venv/bin/python scripts/parse_logs.py

# run dashboard
.venv/bin/streamlit run streamlit_app.py
# → http://localhost:8501

# kill stale streamlit before restart
pkill -f 'streamlit run streamlit_app'
```

**Filesystem layout (Mac):**

- `~/hardcore-chronicles/` — this project.
- `~/hardcore-chronicles/.venv/` — Python virtualenv (gitignored).
- `~/hardcore-chronicles/assets/logs/{vanilla,forge}/` — raw logs (gitignored).
- `~/minecraft-forge/` — live Forge server (logs originate here).
- `~/minecraft/logs/` — vanilla-era logs (read-only at this point).
- `~/playit/docker-compose.yml` — tunnel agent (Docker), unrelated to this repo but contextually adjacent.

**Things easy to break:**

- The PvP-categorization keys on `by <PlayerName>` substring. If a new player joins with a name overlapping a vanilla entity, fix the categorizer in `parse_logs.py:categorize()`.
- The midnight-crossing heuristic in `parse_logs.py:parse_ts()` assumes vanilla logs never go backward by >12 h within a file. Don't import logs from a clock-drifted source without manual review.
- The hardcore cutoff (`2026-05-05 21:37`) is a magic constant. If the server moves or the cutoff changes, update `HARDCORE_FROM` in `parse_logs.py` and re-run.
- `categoryorder="array"` on the death-messages chart is the only thing keeping the global desc sort working under `color="category"`. Removing it brings the bug back silently.

**Likely next user prompts:**

- "Deploy it / I pushed it to GitHub, here's the URL"
- "Add icon X for mob Y"
- "The auditor flagged number N — please verify"
- "Add a new stat: <thing>"
- "Polish [section] further"

For any "add a stat" request: check whether the data already exists in `data/`, add to the Streamlit app, do **not** add it to `parse_logs.py` unless it requires new raw-log signal. Then update `METHODOLOGY.md` §5 if a new CSV column is introduced.
