# Audit Report

## Executive Summary

The project is well-organized, well-documented, and visually polished. The Streamlit app runs cleanly (no exceptions on either page), the architecture is clear (logs → `parse_logs.py` → CSVs → multi-page Streamlit), and the methodology document is unusually thorough for a personal dashboard.

However, the audit surfaced **one material correctness bug in the parser pipeline** that affects the headline numbers shown in `README.md` and `data/summary.csv`: the parser ingests Forge **debug-log** files (`debug-N.log.gz`) in addition to the main server logs. Because the same world-creation / death lines are mirrored into both files, the dataset contains **5 phantom (empty) "skipped" worlds** and **2 duplicated death rows**. The correct figures are **44 hardcore worlds attempted (not 49)** and **51 total deaths (not 53)**.

The bug is largely hidden in the UI because the default "<15 min active" toggle filters the phantom worlds out — but the README badges, `summary.csv`, METHODOLOGY ground-truth, and the post-toggle "View all worlds" expander all expose it.

Two smaller correctness issues in METHODOLOGY.md (an off-by-one world-number in the "Dragon kill" example, and a broken spot-check snippet) are documented below.

## Readiness Verdict

Status: **Mostly ready, minor fixes needed**

The dashboard renders correctly, the design and tone match the documented audience, and the methodology is reproducible. But the README's hero badges and `summary.csv`'s totals are wrong because of the debug-log double-ingestion. That's a small parser fix (one line in `collect_log_paths`) plus a CSV re-generation, after which the project is in shape to share.

## Repository Context Reviewed

Files and folders inspected (everything *except* `auditor_1/` and `auditor_3/`):

- Top-level docs: `task.md`, `README.md`, `METHODOLOGY.md`, `PLAYSTYLE.md`, `BACKLOG.md`.
- Entry points: `Global_Stats.py` (page 1), `pages/2_Latest_World.py` (page 2).
- Parsers: `scripts/parse_logs.py`, `scripts/parse_snapshot.py`.
- Data: every file under `data/` (`summary.csv`, `worlds.csv`, `deaths.csv`, `death_messages.csv`, `players.csv`, `pvp.csv`, `advancements.csv`, `live_stats_summary.csv`, `live_stats_detail.csv`, `live_advancements.csv`).
- Raw inputs: `assets/logs/{vanilla,forge}/` (directory listing only — verified file counts and the presence of `debug-*.log.gz`).
- Config: `requirements.txt`, `.gitignore`, `.streamlit/`.

Reproducibility check actually performed:
- Re-ran all METHODOLOGY §7 spot-checks against committed CSVs (results below).
- Imported `Global_Stats.py` and `pages/2_Latest_World.py` via `streamlit.testing.v1.AppTest`; both ran end-to-end with `exception = ElementList()` (no exceptions) and produced 7+7 plotly charts, 15+36 metrics.
- Verified the parser via partial import (`collect_log_paths()`) to confirm which files it would ingest.
- Did **not** re-run `scripts/parse_logs.py` end-to-end (working rules say "Do not modify project files except `report.md`" — re-running the parser would overwrite committed CSVs).

Files expected but not found: none. (The `assets/` payload is present locally even though `.gitignore`d.)

## Source Data Audit

**Provenance & sufficiency.** The data is the right shape for the stated goal. All ten CSVs trace back to either (a) Minecraft server logs at `assets/logs/{vanilla,forge}/` parsed by `scripts/parse_logs.py`, or (b) a single live-world player-stats snapshot at `assets/snapshots/live-world/...` parsed by `scripts/parse_snapshot.py`. Both inputs are gitignored and shipped out-of-band, exactly as METHODOLOGY §2 says.

**Assumptions made explicit.** The hardcore cutoff (`2026-05-05 21:37`), the three tracked usernames, the death-verb list, and the categorization keyword lists are all hard-coded near the top of `scripts/parse_logs.py` with comments explaining provenance. The midnight-crossing heuristic for vanilla logs is documented in both code and METHODOLOGY §8.

**Limitations acknowledged.** METHODOLOGY §8 ("Known caveats") covers the right things: spectator-mode follow-on deaths, PvP attribution edge cases, active-minute rounding, the deliberate pre-hardcore death exclusion, single-world snapshot coverage, and `fly_one_cm` not being elytra-specific. This is unusually thorough for a personal project.

**Correctness issue found.** `scripts/parse_logs.py:collect_log_paths()` does `d.glob("*.log.gz")`, which picks up **both** the main rotated logs (`2026-05-16-N.log.gz`) **and** the Forge debug rotated logs (`debug-N.log.gz`). The debug log mirrors INFO-level lines from the main log, so every world-creation, join, leave, advancement, and death line on May 16 is parsed twice. Concrete impact in committed `data/worlds.csv`:

```
world_num=38, start=2026-05-16T02:02:24, outcome=skipped, active=0.0, src=2026-05-16-5.log.gz
world_num=39, start=2026-05-16T02:02:24, outcome=died,    active=85.6, src=debug-5.log.gz
world_num=40, start=2026-05-16T15:53:12, outcome=skipped, active=0.0, src=2026-05-16-4.log.gz
world_num=41, start=2026-05-16T15:53:12, outcome=skipped, active=1.0, src=debug-4.log.gz
world_num=42, start=2026-05-16T15:54:20, outcome=skipped, active=0.0, src=2026-05-16-3.log.gz
world_num=43, start=2026-05-16T15:54:20, outcome=died,    active=1.3, src=debug-3.log.gz
world_num=44, start=2026-05-16T15:56:08, outcome=skipped, active=0.0, src=2026-05-16-2.log.gz
world_num=45, start=2026-05-16T15:56:08, outcome=skipped, active=3.5, src=debug-2.log.gz
world_num=46, start=2026-05-16T15:59:46, outcome=skipped, active=0.0, src=2026-05-16-1.log.gz
world_num=47, start=2026-05-16T15:59:46, outcome=skipped, active=0.6, src=debug-1.log.gz
```

Worlds 38, 40, 42, 44, 46 are **phantom**: a second "creating new world" event from the debug log fires on the same second as the real one, opening and immediately closing a 0-second world. The advancement parser is *protected* (it dedupes by `(world_num, player, advancement)` in `parse_logs.py:374-380`), but world boundaries and death rows are not — `data/deaths.csv` contains two duplicate rows (world 39 "MurzichAI was slain by Zombie" and world 43 "MurzichAI was slain by axantroff", each appearing once with `is_first_in_world=YES` and once with `NO`).

**Trustworthiness.** The data is broadly trustworthy *for the bulk of the dataset* — vanilla and forge May 5–15 logs are unaffected. The May 16 portion is inflated. Specifically:

| Metric | Committed value | Real (de-duplicated) | Drift |
| --- | --- | --- | --- |
| `total_worlds_attempted` | 49 | 44 | +5 phantom skipped |
| `worlds_skipped` | 20 | 15 | +5 |
| `worlds_died` | 29 | 29 | — |
| `failure_rate_pct` | 59.2 | 65.9 | −6.7 pp understated |
| `total_deaths` | 53 | 51 | +2 dup rows |
| `players.MurzichAI.total_deaths` | 27 | 25 | +2 |
| `total_active_minutes` | 1622.6 | 1622.6 | — (phantoms add 0 min) |

## Methodology Audit

**Clarity and goal.** METHODOLOGY.md is unusually well-structured — an ASCII pipeline diagram, source-of-truth tables, explicit verb-and-keyword catalogs, eight numbered spot-checks. A new contributor can orient themselves in 15 minutes.

**Correctness of computations (independent reading of `scripts/parse_logs.py`).**
- Hardcore cutoff: correctly applied in `write_csvs()` at line 292 (`hc = [w for w in worlds if w["start"] >= HARDCORE_FROM]`).
- World partitioning: `build_worlds()` walks events sequentially, attaches deaths to the world that was "open" at that point, and caps the last world's `window_end` at `end_of_data` rather than `now()` — which correctly avoids the unclosed-session inflation called out in §4.
- Event sort order `W < J < A < D < L` in `parse_events()` correctly ensures a same-second world-creation opens before any death is attributed (this is what spot-check §7.5 validates; confirmed `collisions == 0`).
- Active-minutes algorithm: per-player intervals → merge across players → sum. The malformed-stream handling (two J's without an L, or trailing J without L) is correct and explicit. Spot-checked against world #15 (the Dragon-kill — 1627 wall vs 208 active min).
- Categorization: the priority-ordered loop in `categorize()` (PvP > Mob > Environment > Other) is correct, and the keyword lists are reasonable. No "Other"-bucket worlds appear in `data/worlds.csv`. ✓
- Advancements dedup: `seen_per_world` keyed on `(world_num, player, advancement)` correctly prevents repeat broadcasts after relog. ✓

**Methodology issues found.**

1. **METHODOLOGY §5.2 example refers to the wrong world number.** It claims "World #16 (Dragon kill). Wall-clock 1627 min, active 208 min." But `data/worlds.csv` row with that signature is **world #15** (`start=2026-05-10T19:02:43, first_death_at=2026-05-11T22:09:46, ...was killed by Ender Dragon using magic, wallclock=1627.0, active=208.1`). World #16 in the data is the next world (a 14-min Creeper death). The spot-check at §7.3 inherits the same off-by-one (`grep '^16,' data/worlds.csv`). The exact death message also differs slightly from §7.3's prose: data shows `was killed by Ender Dragon using magic`, not `was killed by Ender Dragon`.

2. **METHODOLOGY §7.5 spot-check snippet fails as written.** The snippet uses `pd.read_csv(... parse_dates=['start_time','first_death_at'])`, but because `first_death_at` is empty for 20 skipped worlds, pandas leaves the column as `object` and the subsequent `.dt.floor('s')` raises `AttributeError: Can only use .dt accessor with datetimelike values`. Fix is to use `errors='coerce'` (or `pd.to_datetime` post-read) and filter `notna()`. With that fix, the underlying check passes (`collisions == 0`).

3. **METHODOLOGY §7.1 / §7.9 baseline numbers (49 / 29 / 20 / ~27h) accept the inflated dataset.** The ground-truth row "worlds: 49 hardcore" is consistent with the data only because of the parser bug above. The auditor running §7.1 verbatim against the current CSVs sees `29 died / 20 skipped` and concludes "passes" — but the real numbers are 29 / 15 / 44. Once the parser bug is fixed, the methodology ground-truth must be re-stated.

4. **§7.9 "both toggles OFF" no longer maps to the UI** — the PvP toggle was removed (per `task.md` §4 #4), and METHODOLOGY §6 itself notes this, but §7.9 still says "With both **OFF**: should return to 49 / 29 / 20 / ~27h." Actual app reading: 47 / 27 / 20 / 25.9h (PvP-categorized first deaths are hardcoded out, removing worlds #17 and #43).

**Reproducibility.** Strong. Both parsers are pure functions of their inputs (no external network, no clock-dependent logic except an `end_of_data` fallback that uses observed events, not `now()`). The recipe in METHODOLOGY §9 is correct except for the §7.5 snippet issue above.

## Results Audit

Verified directly against committed CSVs (METHODOLOGY §7 spot-checks):

| Spot-check | Expected | Observed | Verdict |
| --- | --- | --- | --- |
| §7.1 worlds outcome breakdown | 29 died / 20 skipped | 29 / 20 | ✓ (matches but inflated by parser bug, see Data §) |
| §7.1 deaths.csv rows | 53 | 53 | ✓ (matches but inflated by 2 dup rows) |
| §7.1 first deaths | 29 | 29 | ✓ |
| §7.2 hardcore cutoff | no row before cutoff | none | ✓ |
| §7.3 Dragon-kill row | 16 / 1627 / 208 | world is **#15**, values otherwise correct | ✗ off-by-one in doc |
| §7.4 sum of first-deaths | 29 | 29 | ✓ |
| §7.5 same-second collisions | 0 | snippet errors; with fix, 0 | ✗ snippet broken |
| §7.6 categories present | '', Mob, Environment, PvP | 20 / 21 / 6 / 2 | ✓ no "Other" |
| §7.7 advancements | 500 / ≤49 / 29 unique | 500 / 28 / 29 | ✓ |
| §7.8 snapshot play minutes | ~340 (148 + 100 + 97) | 344.8 (148.2 + 100.1 + 96.5) | ✓ |
| §7.9 toggles-off baseline | 49 / 29 / 20 / ~27h | app: 47 / 27 / 20 / 25.9h | ✗ stale (PvP toggle removed) |

Internal consistency:

- `summary.csv` totals reconcile against `worlds.csv` and `deaths.csv` within rounding (sum of `active_minutes` = 1622.4 in worlds.csv vs 1622.6 in summary.csv — 0.2-minute drift attributable to 1-decimal rounding per row).
- `players.csv` first/total/PvP counts reconcile against `deaths.csv` and `pvp.csv` exactly.
- `unique_death_messages = 19` matches `wc -l data/death_messages.csv = 20` (19 + 1 header). ✓

Surprising / misleading:

- **README badge "49 worlds attempted | 29 ended in death | 20 rerolled"** is the most visible incorrect surface. Once the parser is fixed, these become 44 / 29 / 15.
- **Page 2 "Items Crafted" = 23.4k** for one player in one world is mathematically correct (Minecraft increments `crafted` per individual recipe execution, and stack-crafts count each output) but reads as surprising — a future polish pass could add a caption.

## Visualization and Presentation Audit

**Strengths.**

- **Visual identity is coherent and on-brand for Minecraft.** Gold accents (`#FFAA00`) for hero numbers and titles, redstone red for hostiles, lava orange for environment, diamond cyan and grass green for player accents, obsidian dark background. The card "inventory slot" treatment (stone-colored borders with subtle gold-glow text shadows) lands well and matches `task.md §5` exactly.
- **Storytelling layout on page 1.** Hero metrics → temporal density → cause-of-death bar + Mob/Env donut side-by-side → time-to-death histogram → progression funnel → fastest-progression table + per-player unique advancements → highlight cards → per-player tally → key insights → browseable table. The narrative arc ("we attempted a lot, we mostly died, here's how, here's how far we got, here's who") is intuitive.
- **Per-player color coding is consistent.** MurzichAI=red, axantroff=cyan, trofimova2002=green across both pages, in cards and bars.
- **Death-message bar chart is globally sorted desc.** Locking `categoryorder="array"` with the pre-sorted label list (page 1 line 304-307) is the right fix for Plotly's grouped-by-color default behavior. Comment on line 282-283 explains why — load-bearing context for future contributors.
- **Page 2 player cards are nicely compact.** Three columns, each with a 2×6 grid of small metrics, with hero `play_minutes` under the player name. The segmented "All Players / per-player" control on the leaderboards is a clean perspective toggle.
- **Key Insights cards on both pages are not duplicative of hero metrics** — they pull share-of-top-cause, top-3 cumulative share, only-once unlocks, deadliest specific enemy, cruelest gap. This is the "fun facts" panel done right per `task.md §5`.
- **Pages explain their own scope.** Page 2's caption ("The one hardcore world out of 49 whose stats survived the rerolls") manages user expectation immediately.

**Weaknesses.**

- **Emoji-in-label spacing inconsistency.** The death-message labels render as `<icon><two-spaces><player>` (e.g. `🟢  <player> was blown up by Creeper`). Most look fine but the multi-codepoint emojis like ⚔️ render with variable width across platforms. Minor.
- **Page 2 "Items Crafted: 23.4k"** without a `help=` tooltip explaining that crafted = recipe executions (not unique recipes) invites confusion.
- **Movement Profile stacked bar (page 2)** uses 7 colors; without a per-mode tooltip, the order (Walk / Sprint / Air / Fall / On Water / Under Water / Sneak) is hard to read at the small sizes. Currently the legend orientation is horizontal at the bottom — fine for desktop, will wrap on mobile.
- **`use_container_width` deprecation warnings.** Streamlit 1.50 emits 8 deprecation warnings per page-1 render. They don't break anything yet, and BACKLOG #8 already tracks this. Won't surprise auditors / friends.
- **Default toggle behavior obscures the parser bug.** With "Exclude <15 min active" ON (the default), all 5 phantom worlds disappear from the UI. That's lucky for current end-users but means the README badge can drift away from what the dashboard shows. A drive-by reader who toggles the filter off will see 47 worlds, while the README says 49.
- **No "data last updated" timestamp** on either page. Page 2 mentions "Snapshot taken 2026-05-16" in prose but no automatic provenance line. Low priority — the dataset is small enough that this isn't a freshness concern yet.

**Polish.** This already looks like a shippable artifact, not a notebook screenshot. The fonts, padding, and color choices are deliberate and consistent.

## Audience Fit

`task.md §3` describes the audience explicitly: three Minecraft hardcore friends aged 23–25 from Belarus/Russia, two guys and a girl, close enough that the dashboard's "tilting" / "you've gotta be kidding me" / "cruelest gap" / "spectator goofing" register reads as friend banter rather than analytics-speak. `task.md §4` also lists hard tone rules (no "Survived", no leaderboard framing, no medals).

Evaluating against that:

- **Interesting** — yes. The 49-attempts-zero-wins arc is inherently a story, and the funnel ("Stone Age 100% → Sweet Dreams 80% → … → The End 5%") makes the progressive gap tangible.
- **Engaging** — yes. The Cruelest Gap card, "Only-once unlocks" highlights, and per-player tally cards give the audience things to react to.
- **Informative** — yes, with one caveat: the headline counts are wrong (see Source Data audit). Friends may not notice, but auditors will.
- **Easy to understand** — yes for page 1; page 2 has more counters than story (a future Role Signatures panel per `PLAYSTYLE.md` would help).
- **Memorable** — likely yes. The gold-on-obsidian color palette is distinctive, and the death-message bar chart with emojis-by-cause is genuinely funny on its own.
- **Tone rules respected** — confirmed. No instances of "survived" in `Global_Stats.py`; outcomes are labeled "Died" / "Rerolled" / "Skipped (no death)". The per-player section is titled "Per Player" with first-deaths called "run-ending" rather than "fails". Sort is by ascending first-deaths (smallest first), which gently avoids podium-style framing. ✓
- **Cultural register** — the friend-banter language is preserved (cf. `task.md §3` directive). External eyes won't read it as hostile.

**Worth sharing in current state?** Almost. Fix the parser-bug headline numbers and one off-by-one in METHODOLOGY, then yes.

**Likely to generate useful feedback from friends?** Yes — the per-player tally and Cruelest Gap will draw direct reactions. The richer page 2 will draw "why isn't *my* signature stat there yet" feedback, which is exactly the input `PLAYSTYLE.md` / `BACKLOG.md` are organized around.

## Strengths

1. **Documentation discipline.** Three layered docs (`task.md` for why, `METHODOLOGY.md` for how, `README.md` for what) with no duplication. `BACKLOG.md` and `PLAYSTYLE.md` capture in-flight context cleanly.
2. **Parser is reproducible and well-commented.** Pure-function design, explicit constants near the top, no `now()` dependency that would cause non-determinism, dedup logic for advancements.
3. **Visual identity is intentional and consistent.** Minecraft block colors, monospace, inventory-slot card aesthetic.
4. **Both pages run end-to-end with no exceptions.** Verified via `streamlit.testing.v1.AppTest`.
5. **Tone constraints are visibly enforced in code.** No "survived" wording, neutral per-player framing, PvP first-deaths hardcoded out without UI mention.
6. **CSVs round-trip and reconcile internally** within rounding tolerance (see Results §).
7. **METHODOLOGY's 8-step spot-check format is a great audit handoff** — even though two of the checks are stale, the structure itself is the right pattern.

## Issues and Risks

### Confirmed issues

#### Issue 1 — Parser ingests Forge debug logs, inflating world & death counts

- **Severity:** High
- **Area:** Data / Reproducibility / Results
- **Description:** `collect_log_paths()` globs `*.log.gz` and matches both main rotated logs (`2026-05-16-N.log.gz`) and Forge debug rotated logs (`debug-N.log.gz`). The debug log mirrors INFO-level lines, so world creations and deaths are parsed twice for May 16. Result: 5 phantom "skipped" worlds with `active=0.0` inserted into `worlds.csv`, plus 2 duplicate death rows in `deaths.csv`. Cascades into wrong totals in `summary.csv`, `players.csv`, and the README badges.
- **Evidence:**
  - `scripts/parse_logs.py:148` — `paths.extend(sorted(d.glob("*.log.gz")))`.
  - `ls assets/logs/forge/ | grep -c debug` = 5 files (`debug-1.log.gz` through `debug-5.log.gz`).
  - `data/worlds.csv` lines 39-49: pairs at identical `start_time` differing only in `source_log` (one ends `2026-05-16-N.log.gz`, the other ends `debug-N.log.gz`).
  - `data/deaths.csv` contains 2 duplicate pairs: world 39 ("MurzichAI was slain by Zombie") and world 43 ("MurzichAI was slain by axantroff"), each appearing once from each log file.
  - Numeric impact table in Source Data audit above.
- **Recommended fix:** In `scripts/parse_logs.py:collect_log_paths()`, exclude debug-prefixed files. One-liner:
  ```python
  paths.extend(sorted(
      p for p in d.glob("*.log.gz") if not p.name.startswith("debug")
  ))
  ```
  Then re-run `python scripts/parse_logs.py`, regenerate `data/`, and update README badges to **44 / 29 / 15**. Update METHODOLOGY §7.1 ground-truth to match.

#### Issue 2 — METHODOLOGY §5.2 / §7.3 cite world #16 but Dragon-kill is world #15

- **Severity:** Medium
- **Area:** Methodology / Presentation
- **Description:** METHODOLOGY's "Concrete example — World #16 (Dragon kill)" and the §7.3 spot-check `grep '^16,' data/worlds.csv` both refer to world 16, but the world with `wallclock=1627, active=208` and Ender Dragon death is **world 15**. The §7.3 prose also abbreviates the death message ("was killed by Ender Dragon") while the CSV shows "was killed by Ender Dragon using magic".
- **Evidence:** `grep '^15,' data/worlds.csv` → matches; `grep '^16,' data/worlds.csv` → unrelated Creeper death at 14 active minutes.
- **Recommended fix:** Update METHODOLOGY §5.2 and §7.3 to "World #15", update the death-message phrasing to match.

#### Issue 3 — METHODOLOGY §7.5 spot-check snippet errors on empty `first_death_at`

- **Severity:** Low
- **Area:** Methodology / Reproducibility
- **Description:** `parse_dates=['start_time','first_death_at']` leaves `first_death_at` as `object` because skipped worlds have empty strings; subsequent `.dt.floor('s')` raises `AttributeError`.
- **Evidence:** Reproduced in this audit's Bash check; underlying invariant holds (0 collisions) once the snippet is fixed.
- **Recommended fix:** Replace the read with `pd.read_csv('data/worlds.csv')` then `w['first_death_at'] = pd.to_datetime(w['first_death_at'], errors='coerce')` and filter `notna()` before the comparison.

#### Issue 4 — METHODOLOGY §7.9 expected toggles-OFF numbers are stale

- **Severity:** Low
- **Area:** Methodology / Presentation
- **Description:** `§7.9` says "With both **OFF**: should return to 49 / 29 / 20 / ~27h" — but the PvP toggle was removed (per `task.md §4 #4`) and is now hardcoded ON. With the remaining toggle OFF, the app shows 47 / 27 / 20 / 25.9h. After Issue 1 is fixed, the post-fix expected becomes 42 / 27 / 15 / ~26h.
- **Evidence:** AppTest reading reported in Results audit.
- **Recommended fix:** Rewrite §7.9 to state "with the `<15 min` toggle OFF and PvP hardcoded out, expected: NN / NN / NN / NNh".

#### Issue 5 — `summary.csv:total_active_minutes` (1622.6) differs from sum over `worlds.csv` (1622.4) by 0.2 min

- **Severity:** Low
- **Area:** Results
- **Description:** Cosmetic — `worlds.csv` rounds `active_minutes` per row to 1 decimal, while `summary.csv` recomputes the total from raw seconds. Across 49 rows the per-row rounding drift accumulates to ~12 seconds.
- **Evidence:** `awk` sum of column 10 in `worlds.csv` = 1622.4; `summary.csv:total_active_minutes` = 1622.6.
- **Recommended fix:** Either round `summary.total_active_minutes` from the sum of `worlds.active_minutes` (so they match), or document the difference. Low priority.

### Possible risks (not confirmed)

#### Risk A — Debug-log ingestion may also have inflated earlier dates if anyone retains old `debug-N.log.gz`

- **Severity:** Medium (becomes High if it happens)
- **Area:** Data / Reproducibility
- **Description:** The current dataset's only collision dates are May 16 because the user appears to have only retained debug rotations from that day. If a future audit run uses an older `assets/` snapshot that contains more debug files, the inflation propagates further. The fix in Issue 1 is preventive.
- **Recommended action:** Apply Issue 1 fix unconditionally.

#### Risk B — Categorization keyword overlap (`wither` is in both MOB_KEYWORDS and ENV_KEYWORDS)

- **Severity:** Low
- **Area:** Methodology
- **Description:** `parse_logs.py:103` lists `"wither"` under both `MOB_KEYWORDS` (the boss) and `ENV_KEYWORDS` (the wither effect). Because Mob is checked first in `categorize()`, any "withered away" death would be tagged Mob, which is debatable (suspicious-stew kills can cause withered-away). No instance exists in the current dataset, but worth a comment.
- **Recommended action:** Add a code comment noting the intentional precedence, or remove `wither` from `ENV_KEYWORDS` as dead code.

#### Risk C — PvP categorization assumes player names don't collide with vanilla entity names

- **Severity:** Low
- **Area:** Data / Methodology
- **Description:** Already flagged in METHODOLOGY §8 and `task.md §8`. Current player names are safe; adding a new player named e.g. "Husk" or "Wolf" would silently mis-categorize.
- **Recommended action:** Add a startup assert in `parse_logs.py` that `PLAYERS` ∩ entity-display-name list = ∅.

#### Risk D — `use_container_width` deprecation will eventually break

- **Severity:** Low
- **Area:** Presentation / Reproducibility
- **Description:** Streamlit's deprecation prints suggest removal after 2025-12-31. The replacement (`width="stretch"`) isn't yet a clean drop-in on `st.plotly_chart` — BACKLOG #8 already tracks this.
- **Recommended action:** Track in backlog as already done; no audit-blocking action.

## Missing Context

- **Deployed Streamlit URL not yet live.** `task.md §7` documents this as an open item; not a blocker for an audit, but the audit cannot validate "feels right when shared via public URL".
- **No `live_advancements.csv` schema example** in `data/`. The CSV is referenced in METHODOLOGY §5b.3, and was confirmed present and loadable via AppTest, but the audit did not exhaustively sample its contents.
- **The "5 friends review" persona is just `task.md §3`.** The audience profile is sufficient for tone calibration but is not split into "primary reviewer" vs "casual scroller" — fine for this project's scope, just noting.

## Recommended Fixes Before Sharing

In priority order:

1. **Fix the debug-log ingestion bug** in `scripts/parse_logs.py:collect_log_paths()` and regenerate `data/`. Update the README badges (49→44, 20→15) and `summary.csv` (`total_worlds_attempted`, `worlds_skipped`, `failure_rate_pct`, `total_deaths`, `players.MurzichAI.total_deaths`). *(Issue 1, High.)*
2. **Update METHODOLOGY.md** §5.2 / §7.3 from world #16 to world #15 with the correct death phrasing; fix §7.5 snippet; rewrite §7.9 baseline numbers. *(Issues 2, 3, 4.)*
3. **Re-state METHODOLOGY §7.1 ground-truth** to match the post-fix CSVs (29 / 15 / 44 / 51 / ~27h).
4. **Reconcile `summary.csv:total_active_minutes` with the sum over `worlds.csv`** so auditors don't see a 0.2-min drift. *(Issue 5.)*
5. **Add a comment** in `parse_logs.py` explaining the `wither` keyword overlap and the deliberate precedence. *(Risk B.)*
6. **(Optional) Add a `help=` tooltip to page 2's "Items Crafted"** explaining the recipe-execution counting semantics, so the 23.4k number doesn't surprise readers.

After 1–3, the project is in shape to share. 4–6 are polish.

## Final Notes

- The codebase reads like it was authored carefully with auditors in mind: identifiers are descriptive, constants are pulled to module top, the comments answer "why" not "what". That's not common in personal projects and it materially shortened this audit.
- The methodology document deserves a callout — the 8-step spot-check format is a model handoff pattern. Even though two of the checks have stale numbers, *the structure itself* makes it easy to detect drift.
- The "active minutes" computation is the project's most interesting analytical move (correctly catching the overnight-idle-inflation problem) and is implemented carefully. Worth keeping front-and-center in any external write-up.
- After the parser fix, the headline narrative becomes slightly more striking, not less: **44 hardcore worlds, 29 ended in death (65.9% failure rate), 15 rerolls without a single death.** The story is the same, just sharper.
