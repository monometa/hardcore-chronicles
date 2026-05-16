# Audit Report

## Executive Summary

The project is well documented, has a clear audience, and the local parser outputs are reproducible from the bundled `assets/` directory. The Streamlit pages also execute without runtime errors in a lightweight AppTest run.

However, the project is not ready to share yet. The most important issue is that the log parser appears to ingest duplicated normal/debug Forge logs as separate evidence. This inflates the stated "49 worlds" story, creates zero-duration skipped worlds, and double-counts at least some death/PvP events. Until that is fixed and the CSVs are regenerated, the headline numbers are not trustworthy enough for external review.

## Readiness Verdict

Status: Not ready, major fixes needed

The dashboard is close in structure and presentation, but the source-data pipeline has a blocking correctness issue. Fix duplicate log ingestion first, regenerate all derived CSVs, then update the methodology spot-checks and presentation wording before sharing.

## Repository Context Reviewed

Reviewed:

- `auditor_1/task.md`
- `task.md`
- `README.md`
- `METHODOLOGY.md`
- `PLAYSTYLE.md`
- `BACKLOG.md`
- `.streamlit/config.toml`
- `requirements.txt`
- `Global_Stats.py`
- `pages/2_Latest_World.py`
- `scripts/parse_logs.py`
- `scripts/parse_snapshot.py`
- `data/summary.csv`
- `data/worlds.csv`
- `data/deaths.csv`
- `data/death_messages.csv`
- `data/players.csv`
- `data/pvp.csv`
- `data/advancements.csv`
- `data/live_stats_summary.csv`
- `data/live_stats_detail.csv`
- `data/live_advancements.csv`
- Local raw inputs under `assets/logs/` and `assets/snapshots/`

Per `auditor_1/task.md`, I did not inspect the contents of `auditor_2/` or `auditor_3/`.

Expected but not present as committed/shareable artifacts:

- Raw `assets/` inputs are gitignored and must be provided out of band.
- No screenshot or deployed URL is present.
- No automated verification script or test suite is present.

## Source Data Audit

The intended source data is appropriate for the goal: raw Minecraft server logs for the global history and a live player snapshot for the latest-world page. The repository documents this clearly in `README.md` and `METHODOLOGY.md`.

Positive findings:

- `assets/logs/` and `assets/snapshots/` are present locally.
- Running the parser logic into temporary directories reproduced the committed CSVs byte-for-byte.
- The committed CSVs are internally coherent on basic checks: 49 `worlds.csv` rows, 29 first-death rows, 53 total death rows, no `Other` death categories, no duplicate `world_num`, and first-death rows in `deaths.csv` match `worlds.csv`.

Blocking data issue:

- Several `debug-*.log.gz` files duplicate the same world-creation, join/leave, advancement, and death lines as matching regular `2026-05-16-*.log.gz` files. `scripts/parse_logs.py` reads all `*.log.gz` files and has no cross-file deduplication. The result is duplicated world starts in `data/worlds.csv`, including zero-minute skipped worlds immediately followed by real worlds at the same timestamp.

Diagnostic impact:

- Current committed summary: 49 hardcore worlds, 29 died, 20 skipped, 53 deaths.
- Diagnostic regeneration excluding `debug-*.log.gz`: 44 hardcore worlds, 29 died, 15 skipped, 51 deaths.
- This does not prove the final corrected count without owner confirmation, but it does prove the current parser has no reliable policy for duplicate normal/debug logs.

Data limitations are mostly documented, especially that detailed snapshot stats cover only one world. Missing or weakly documented inputs are listed in "Missing Context."

## Methodology Audit

The high-level methodology is sound: parse source events, partition them into worlds, use first-death as the run-ending event, compute active minutes from the union of player online intervals, and keep raw CSVs available for auditor transparency.

The active-minutes algorithm is well described and implemented in `scripts/parse_logs.py`. The choice to use active minutes instead of wall-clock minutes is appropriate because the server was sometimes idle overnight.

Major methodology gaps:

- Duplicate log handling is absent. The methodology does not say whether normal logs and debug logs can overlap, whether debug logs should be ignored, or whether events should be deduplicated by `(timestamp, kind, player, payload)`.
- `latest.log` handling is brittle for vanilla-style logs without dates. `scripts/parse_logs.py` falls back to the file modification date and preserves microseconds from that metadata, which appears in `data/worlds.csv` and `data/advancements.csv`.
- The auditor spot-check for the Dragon run is stale. `METHODOLOGY.md` says World #16 is the Dragon run, but `data/worlds.csv` has it as World #15.

## Results Audit

The final results are not sufficiently supported until duplicate log ingestion is fixed.

Confirmed supported results:

- There are 29 first-death worlds in the committed data.
- `death_messages.csv` sums to 29 first deaths.
- No pre-hardcore worlds appear in `data/worlds.csv`.
- World #15 is the long Dragon run: wall-clock 1627.0 minutes, active 208.1 minutes.
- AppTest executed both Streamlit pages without reported app errors.

Confirmed unsupported or risky results:

- The headline "49 worlds attempted" and "20 rerolled/skipped" are likely inflated by duplicate debug/regular logs.
- `total_deaths` and `pvp.csv` are affected by duplicate death events. For example, diagnostic regeneration without debug logs reduces total deaths from 53 to 51 and changes PvP pair counts.
- World numbers after the duplicate-log region are unstable if the duplicate policy changes.

## Visualization and Presentation Audit

Strengths:

- The visual identity is coherent with the Minecraft theme: dark background, gold accents, red/orange cause colors, and monospace typography.
- The page layout is clear: hero metrics, daily attempts, death-message bars, cause donut, duration bins, progression, per-player section, and a world browser.
- The latest-world page gives a useful per-player snapshot and makes the "one world only" limitation visible.
- The UI uses `active_minutes` for duration charts, matching the documented canonical metric.

Weaknesses:

- Page 2 uses "Top of the Leaderboards" and a trophy icon, while `task.md` explicitly says the dashboard must not use leaderboard/competition framing.
- The default filter removes all skipped worlds in the current data, so the default global page can underplay the reroll part of the story unless users notice the toggle.
- `use_container_width=True` emitted deprecation warnings during AppTest. With `requirements.txt` using open-ended minimum versions, deployment may eventually pick a Streamlit version where this breaks.
- Page 2 says damage values are "halved" in the footer, but `scripts/parse_snapshot.py` divides damage counters by 10 and `METHODOLOGY.md` documents divide-by-10.

## Audience Fit

The project has unusually strong audience context. `task.md` and `PLAYSTYLE.md` explain who the dashboard is for, why the tone should be playful, and which stats are meaningful to the friend group.

The idea is interesting and shareable: it turns a frustrating hardcore losing streak into a funny, browsable history. The active-time correction, first-death framing, per-player context, and progression milestones are all likely to generate good discussion with friends.

Current blocker for audience fit:

- The numbers need to be trusted before sharing. Friends will likely notice if duplicate rerolls or inflated death counts are later corrected.
- Leaderboard wording conflicts with the stated tone guardrail. Resource/combat comparisons can still work, but the framing should be "group highlights", "most common", or "who did what" rather than leaderboard/podium language.

## Strengths

- Clear project purpose and audience.
- Strong documentation in `task.md`, `README.md`, and `METHODOLOGY.md`.
- Good separation between raw parsing, CSV artifacts, and UI rendering.
- Parser regeneration is deterministic for the current local assets.
- Active-minutes methodology addresses a real measurement problem.
- Data CSVs are transparent and easy to inspect.
- Streamlit pages run locally under AppTest without app errors.
- Presentation is polished enough to be compelling once data correctness is fixed.

## Issues and Risks

### 1. Duplicate debug logs inflate world and death counts

- Severity: Critical
- Area: Data, Methodology, Results, Reproducibility
- Description: `debug-*.log.gz` files duplicate regular Forge logs, but the parser reads both and treats duplicate world-creation events as separate worlds. This creates zero-duration skipped rows and can double-count deaths.
- Evidence from the repository:
  - `scripts/parse_logs.py:148` reads every `*.log.gz`.
  - `data/worlds.csv:39-48` contains repeated `start_time` values from paired regular/debug logs.
  - Raw `assets/logs/forge/2026-05-16-5.log.gz` and `assets/logs/forge/debug-5.log.gz` contain identical world-creation and session lines at `16May2026 02:02:24`.
  - Diagnostic regeneration excluding `debug-*.log.gz` changed totals from 49 worlds / 20 skipped / 53 deaths to 44 worlds / 15 skipped / 51 deaths.
- Recommended fix: Decide the source-of-truth policy. Usually either ignore `debug-*.log.gz` when matching regular logs exist, or deduplicate parsed events across files by `(timestamp, kind, player, payload)`. Regenerate all CSVs and update all headline numbers after the policy is implemented.

### 2. Auditor methodology spot-check is stale

- Severity: High
- Area: Methodology, Reproducibility
- Description: `METHODOLOGY.md` tells auditors to verify the Dragon run as World #16, but the committed data has that run as World #15.
- Evidence from the repository:
  - `METHODOLOGY.md:141-142` and `METHODOLOGY.md:283-287` identify World #16 as the Dragon run.
  - `data/worlds.csv:16` shows World #15 is the Dragon run with `1627.0` wall-clock and `208.1` active minutes.
  - `data/worlds.csv:17` shows World #16 is a short Creeper death.
- Recommended fix: After fixing duplicate log ingestion and regenerating data, update every world-number-specific spot-check to the new final CSV state.

### 3. `latest.log` fallback depends on file metadata

- Severity: High
- Area: Data, Reproducibility
- Description: Vanilla-style `latest.log` has no date in each line. The parser falls back to file modification time when the filename has no date, and preserves metadata microseconds. This can make regenerated CSV timestamps depend on how `assets/` was copied.
- Evidence from the repository:
  - `METHODOLOGY.md:57` says vanilla dates are recovered from filenames.
  - `scripts/parse_logs.py:132-134` uses `fallback_date.replace(...)`.
  - `scripts/parse_logs.py:138-152` appends `latest.log` and sorts by file mtime.
  - `data/worlds.csv:50` has `2026-05-16T23:05:43.817830` from `latest.log`; raw log lines have only `[23:05:43]`.
  - `data/advancements.csv:495-501` carries the same `.817830` microsecond artifact.
- Recommended fix: Do not parse undated `latest.log` without a stable date source. Rename/copy it to a dated archive before parsing, add a manifest mapping undated logs to dates, or require explicit date input. Also zero `microsecond` in `parse_ts()`.

### 4. Presentation violates the no-leaderboard guardrail

- Severity: Medium
- Area: Presentation, Audience Fit
- Description: The project explicitly forbids leaderboard/competition framing, but page 2 and methodology use leaderboard language and trophy/medal framing.
- Evidence from the repository:
  - `task.md:52` says never frame the dashboard as a leaderboard or competition, and says no medals.
  - `pages/2_Latest_World.py:248-252` renders "Top of the Leaderboards" with a trophy icon.
  - `METHODOLOGY.md:218` calls page 2 charts "Top of the Leaderboards".
- Recommended fix: Rename this section to non-competitive language such as "Group Highlights", "Most Common Actions", or "What We Did Most". Remove trophy/medal framing where it suggests ranking people.

### 5. Open-ended dependencies plus Streamlit deprecations reduce deployment reproducibility

- Severity: Medium
- Area: Reproducibility, Presentation
- Description: `requirements.txt` uses minimum versions only. AppTest emitted Streamlit warnings that `use_container_width` should be replaced with `width`.
- Evidence from the repository:
  - `requirements.txt:1-3` uses `streamlit>=1.36.0`, `pandas>=2.0.0`, and `plotly>=5.18.0`.
  - `Global_Stats.py:399` is one of several `st.plotly_chart(..., use_container_width=True)` calls.
  - `pages/2_Latest_World.py:244` and `pages/2_Latest_World.py:320` also use `use_container_width=True`.
  - AppTest emitted the warning: "Please replace `use_container_width` with `width`."
- Recommended fix: Pin exact tested versions before deployment, or update Streamlit calls to the currently supported API and then pin.

### 6. Damage-unit explanation is inconsistent

- Severity: Low
- Area: Methodology, Presentation
- Description: Page 2 footer says damage values are "halved", while code divides by 10 and methodology describes divide-by-10.
- Evidence from the repository:
  - `scripts/parse_snapshot.py:82-83` divides `damage_dealt` and `damage_taken` by 10.
  - `pages/2_Latest_World.py:481-482` says damage values are halved.
- Recommended fix: Change the footer to match the implemented conversion, or adjust the conversion if the footer is the intended interpretation.

### 7. Raw cutoff evidence is not in the repository

- Severity: Low
- Area: Data, Missing Context
- Description: The hardcore cutoff is central to inclusion/exclusion, but the repository does not include direct server-properties evidence for the exact flip time.
- Evidence from the repository:
  - `scripts/parse_logs.py` hardcodes `HARDCORE_FROM = datetime(2026, 5, 5, 21, 37)`.
  - `METHODOLOGY.md` says the cutoff comes from server state/history, but no raw proof is included in the repo.
- Recommended fix: Add a short note, screenshot, config excerpt, or log/commit reference showing why `2026-05-05 21:37` is the correct cutoff.

## Missing Context

- A stable source-of-truth policy for debug logs versus regular logs.
- Direct evidence for the hardcore cutoff time.
- Confirmation of the intended final world count after duplicate-log handling.
- A deployment URL or screenshots of the final rendered dashboard.
- Exact dependency versions used for the tested app.
- An automated smoke-test or verification script that runs both parsers and validates headline invariants.

## Recommended Fixes Before Sharing

1. Fix duplicate log ingestion in `scripts/parse_logs.py`.
2. Regenerate `data/worlds.csv`, `data/deaths.csv`, `data/death_messages.csv`, `data/players.csv`, `data/pvp.csv`, `data/summary.csv`, and `data/advancements.csv`.
3. Re-check all headline metrics and update `README.md`, badges, dashboard copy, and `METHODOLOGY.md`.
4. Replace stale world-number spot-checks, especially the Dragon-run check.
5. Remove leaderboard/trophy/medal framing that conflicts with `task.md`.
6. Make `latest.log` date handling deterministic.
7. Pin exact dependency versions or update deprecated Streamlit API usage.
8. Add a simple verification script for parser regeneration and key invariants.
9. Re-run Streamlit AppTest or a local browser smoke test for both pages.
10. Deploy only after the regenerated numbers are accepted as final.

## Final Notes

The project has a strong concept and the dashboard is already engaging. The blocker is not polish; it is trust in the headline data. Once duplicate log handling is fixed, most remaining issues are straightforward documentation and presentation cleanup.
