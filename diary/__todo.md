## Current goal (Max 1)
### Hermes: Display rolling monthly costs from real data
Real data exists (3 accounts, back to 2021). No mock data needed. Goal: load the CSVs and display a rolling 2-month cost summary in the terminal.

**~~Step 1 — Wire up real data (unblock everything)~~ ✓**
- ~~Fix Makefile: mount `../../external_data/real_data/shared` instead of `$(PWD)/shared`~~
- ~~Verify `make run` can read the CSV files inside the container~~

**~~Step 2 — Load and parse transactions~~ ✓**
- ~~Write BDD feature: "load transactions from CSV"~~
- ~~Implement CSV loader (semicolon-separated, UTF-8 BOM, Swedish headers)~~
- ~~Strip account numbers at ingestion boundary — only friendly names in DuckDB~~
- ~~8115 transactions loaded across 3 accounts, all Behave tests passing~~

**~~Step 3 — Display rolling monthly costs~~ ✓**
- ~~Marimo notebook served inside Docker on port 2718~~
- ~~Reactive account filter, 2-month rolling view~~
- ~~Milestone reached: real numbers visible in notebook~~

**Step 4 — Categorize transactions and produce reproducible report**
- Define keyword → category rules (e.g. HEMKOP → Groceries, TELIA → Telecom)
- Apply rules during ingestion or as a query layer in DuckDB
- Write BDD feature: "categorize transactions"
- Update notebook: costs grouped by category, per account, rolling 2 months
- Add `make report` target: export notebook to HTML/PDF via `marimo export`
- Milestone: see categorized cost report in notebook and as a saved file


## Shortterm goals (Max 3)

**GoPro Tandådalen: edit and upload to Google Photos**
Create movies from GoPro footage of Tandådalen trips with correct GPS positioning and dates, then upload to Google Photos.
- Edit footage in DaVinci Resolve (starting with 2026-05-01)
- Verify/fix GPS metadata and timestamps on output files
- Upload to Google Photos with correct location and date

## Skills: Improvement
### Git commit skill
Build a `/commit` skill that stages, drafts a commit message from the diff, and produces a markdown-formatted commit review before confirming.
- Design skill flow (diff → message draft → review → confirm)
- Write commit review subagent with markdown output
- Test against real commits
- Implement commit splitting: analyze diff and separate renames, refactors, file moves, and functional changes into distinct commits for easier review

Session: start improvement
_On session start  Claude looks at platform engineering, AI sites and the contents of last session and recommends 3 articles to read_

## Active project milestones (Max 3)
- Skills definitions baseline(AI learning)
-  Hermes - See rolling monthly costs calculation for all important accounts
- Hermes - Cost control
- Gopro Tandådalen movie