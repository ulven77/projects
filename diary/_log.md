## 20260510 — April reconciliation closes; accounts.yaml + rule cleanup

**Type of work:** debugging, configuration, writing
**Repos touched:** aisafe/projects

**Session highlights:**
- Switched accounts metadata from JSON to YAML for editable multi-line descriptions; added PyYAML to pyproject; updated categorize.py + report.py to yaml.safe_load
- Reshaped account model: Petra moved from household to external; identified four external Swish counterparts (Linnea, Ella, Johanna, Malin); added swish_alias mechanism so phone numbers are metadata on the account, not separate entries
- Tightened categorization rules to match accounts.yaml: date-bounded historical mortgage rules, blanket pre-2024 LÅN → Internal, specific Family-transfer rules for known external account numbers, kept "467" Swish as catch-all
- Closed April 2026 reconciliation to the öre: tracked +1 319 kr = budget +27 181 kr − 25 862 kr leakage to non-tracked counterparts; documented the deliberate Ulf Personal split categorization

**Significant learnings:**
- SEB transaction exports are in reverse-chronological order (newest first) — opening balance must be derived from the OLDEST April tx in the list, not the last position; verified via SEB portal screenshot
- Swish is a payment method, not a relationship indicator — categorization rules should default to "Swish transfers" and only annotate specific transactions when purpose is known; family-transfer rules belong on direct bank transfers (account numbers), not on Swish phone numbers
- Tracing a chain of transactions by description alone (MEDICINERCEL → Hampus refill → uffe hus → Ella reimbursement) is faster than annotating each leg in isolation; a single economic event can span four transactions across two days

**Pick up next time:** Reconcile May 2026 — first month with the new MAT routing (lön → Matvecka), so the new annotation gets its first real test

---

## 20260509 — Financial advisor pipeline: full build + security review

**Type of work:** coding, configuration, debugging
**Repos touched:** aisafe/projects

**Session highlights:**
- Built the complete three-stage Docker pipeline: extract.py (SEB xlsx/pdf), categorize.py (rule engine + annotations), report.py (13-section Markdown + Mermaid report)
- Implemented discrepancy detection: flow rule violations, uncategorized transactions, monthly limit overruns with exceptions system and discrepancy_log.md
- Wired SEB transfer quirk into flow rules — incoming transfers show account holder name (PETRA RASK/ULF RASK), not account name; added to allowed_sources
- Security review passed: CLAUDE.md scrubbed of surnames/account numbers; RULES.md moved to ~/financials/ (gitignored, outside repo)

**Significant learnings:**
- SEB incoming transfers show the account *holder's* name, not the account name — flow rules must allow both account name and holder names as valid sources
- Docker volume mounts mean host paths like `/home/uven/financials/foo.json` don't exist inside the container — always use the mount path (`/reports/foo.json`)

**Pick up next time:** Commit financial_advisor to GitHub; action the improvements list (cancel subscriptions, identify APPLE COM/BI charges); export Petra personal account

---

## 20260503f — arc42 refresh completed; Step 4 scoped with reproducible report

**Type of work:** writing, planning
**Repos touched:** aisafe/financial_project/hermes, aisafe/projects

**Session highlights:**
- Resumed after context compaction mid-arc42 refresh — applied all remaining corrections:
  Scenario 1 (entry point, DuckDB mount path, removed category references),
  Scenario 2 (Marimo via Docker), Scenario 3 (actual Behave load_transactions tests),
  Deployment View (Marimo inside Docker with port mapping),
  Section 8 (amount format confirmed period decimal, in-memory DuckDB test isolation note),
  ADR-007 updated (Marimo in Docker), ADR-008 added (account number stripping),
  Section 11 amount format risk marked resolved
- Added `make report` (marimo export → HTML/PDF) to Step 4 in `__todo.md`
- Committed and pushed both hermes and projects; all repos clean

**Significant learnings:**
- None new — finalization session

**Pick up next time:** Step 4 — categorize transactions, write BDD feature, update notebook, add `make report`

---

## 20260503e — Hermes: CSV pipeline, Marimo notebook, Behave tests

**Type of work:** coding, devops
**Repos touched:** aisafe/financial_project/hermes, aisafe/projects

**Session highlights:**
- Fixed Makefile to mount real data directory (`../external_data/real_data/shared`)
- Designed architecture: Marimo runs inside Docker with port mapping; account numbers stripped at ingestion boundary
- Implemented CSV loader (`hermes.ingest`): reads 3 Swedbank CSVs, strips account numbers, writes to DuckDB — 8115 transactions
- Marimo notebook (`make notebook`) served at localhost:2718, reactive account filter, rolling 2-month view
- Behave tests use in-memory DuckDB — 3 scenarios, 14 steps, all green
- User confirmed: numbers visible in notebook, data looks correct

**Significant learnings:**
- Privacy by architecture: ingestion runs `--network=none` and strips account numbers before DuckDB; notebook (which needs network to serve UI) never sees sensitive identifiers
- In-memory DuckDB for tests keeps the test target clean and fast without touching real data

**Pick up next time:** Categorize transactions — define keyword rules, apply during ingestion, update notebook to show costs by category

---

## 20260503d — Session-end skill review and diary corrections

**Type of work:** configuration, writing
**Repos touched:** aisafe/skills, aisafe/projects

**Session highlights:**
- Reviewed session-end skill; found it relied on conversation history as primary source, missing full-day work
- Fixed gap detection: now uses `git log --since today` per repo and cross-references against existing session log
- Added step to ask user how the session felt — never infer or invent emotions in the diary
- Corrected today's diary twice: removed invented "the tool works" claim and invented feelings section

**Significant learnings:**
- Conversation history only covers the current Claude session — git log timestamps are the ground truth for what happened across the whole day
- The diary is a personal record; feelings must come from the user, not be fabricated by the tool

**Pick up next time:** Hermes CSV loader — parse three Swedish bank account CSVs, map columns, print rolling 2-month cost summary

---

## 20260503c — Commit skill: first real run, self-caught bug

**Type of work:** configuration, devops
**Repos touched:** aisafe/skills

**Session highlights:**
- Ran `/commit` skill for the first time in anger — it immediately surfaced a broken subagent reference
- `workspace-review` had been renamed to `arc42-review` but the pointer in `commit/SKILL.md` still used the old name
- Fixed reference, updated confirmation prompt to numbered list, committed as single refactor

**Significant learnings:**
- A commit orchestrator that runs a workspace review will catch its own stale references — the skill validated itself on first use

**Pick up next time:** Start Hermes CSV loader — parse three Swedish bank account CSVs, map columns, print rolling 2-month cost summary

---

## 20260503b — Hermes architecture + three new skills

**Type of work:** coding, planning, configuration
**Repos touched:** aisafe/financial_project/hermes, aisafe/skills

**Session highlights:**
- Wrote 453-line `arc42.md` for Hermes: system context, container view, runtime scenarios, deployment view, and ADRs
- Key ADRs: Docker-only (network=none for ingestion), BDD-first, DuckDB over SQLite, Marimo over Streamlit
- Wired up volume mount: container now reads `shared/hellomessage.txt` instead of hardcoded string; BDD scenario updated
- Added `.gitignore` entries for DuckDB file (contains real bank data), SBOM, and generated artefacts
- Built arc42 skill (create + refresh subagents), workspace-review skill, and commit skill from scratch
- Updated `__todo.md`: goal reframed as "real data pipeline with DuckDB + Marimo" (no mock data needed)

**Significant learnings:**
- Marimo is preferred over Streamlit because notebooks are reproducible and exportable — matters when output is a printable monthly report
- DuckDB is the right fit here: embedded, zero-ops, fast on CSV, and safe to keep next to the code (just gitignore the file)
- arc42 ADRs are worth writing early — they make the "why" explicit before the code obscures it

**Pick up next time:** Hermes CSV loader — Step 1 of the real data pipeline

---

## 20260503 — CLAUDE.md on-load not firing

**Type of work:** debugging, configuration
**Repos touched:** aisafe/projects

**Session highlights:**
- Noticed CLAUDE.md on-load sequence (symlink check, diary read) didn't run at session start
- Ran the sequence manually; symlink was intact, no structural issue
- Root cause: behavioral — Claude must treat first message as a trigger to run on-load before responding

**Significant learnings:**
- On-load instructions in CLAUDE.md only fire if Claude actively reads and acts on them before the first response; being in context is not enough

**Pick up next time:** Start Hermes mock data — plan project structure and create two months of realistic financial data

---

## 20260502b — Planning + diary-on-load config

**Type of work:** planning, configuration
**Repos touched:** aisafe/projects, aisafe (USER_SCOPED_CLAUDE.md)

**Session highlights:**
- Added goals to `__todo.md`: GoPro Tandådalen (current), Hermes mock data (future), git commit skill with splitting (future)
- Updated `USER_SCOPED_CLAUDE.md`: Claude now reads diary/log on every session load for automatic context

**Significant learnings:**
- Having Claude read the diary on load removes the need to call `/session start` just to get oriented

**Pick up next time:** Edit GoPro Tandådalen footage in DaVinci Resolve; start with 2026-05-01 session

---

## 20260502 — Skills build: session + create-claude + create-skill improvements

**Type of work:** coding, configuration, devops
**Repos touched:** aisafe/skills, aisafe/projects

**Session highlights:**
- Built `session` skill from scratch: start/end router, diary-writer, session-logger, templates, full subagent structure
- Built `create-claude` skill: draft and review CLAUDE.md files at any scope (user, project, directory)
- Improved `create-skill` intent-clarification flow (committed: "Improve create-skill intent-clarification flow")
- System work: fixed apt mirror (se→main), installed DaVinci Resolve deps, fixed Ghostty xterm-ghostty terminfo, configured gdm3 display server

**Significant learnings:**
- Splitting diary-writing and session-logging into separate subagents (prose vs. structured data) keeps each focused and easier to tune
- Regional apt mirrors can silently serve stale package lists — switching to archive.ubuntu.com unblocked the system upgrade
- DaVinci Resolve on Linux requires libxcb-cursor0 and deliberate X11/Wayland configuration

**Pick up next time:** Commit and push pending skills changes (create-claude, session, deleted template/SKILL.md), then edit GoPro footage from 2026-05-01 in DaVinci Resolve

---
