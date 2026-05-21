## 20260521 — Account-flow report + observed deviations between intent and reality

**Type of work:** coding, writing, research
**Repos touched:** ~/financials (account_flows.yaml + account-flow.md + generate_account_flow_report.py), aisafe/projects (__todo.md)

**Session highlights:**
- Built `~/financials/generate_account_flow_report.py` (285 lines) that produces `account-flow.md` from `account_flows.yaml` + `accounts.yaml`. Renders a Mermaid flowchart with subgraphs (SEB-konton / Lysa / Externa / Personliga konton), edge labels (amount + description_pattern), purpose-coded line styles, plus full tables for active and closed flows.
- Iterated layout: `flowchart TD` → `flowchart LR` (left-to-right per user request), then moved Uffe betalkonto + Petra personal into a dedicated "Personliga konton" subgraph declared last so they render at the bottom of the LR layout (Mermaid stacks subgraphs in declaration order).
- Added missing edge to `account_flows.yaml`: Lön → Petra personal allowance. Verified in data first — actual cadence is sporadic (3 outgoing tx in last 12 mo from lön: −500, −9 000, −3 000 kr), not the monthly 3 000 kr that accounts.yaml's intended_behaviours claims.
- Added a `deviations:` block to `account_flows.yaml` and a `render_deviations()` function to the generator. Three observed deviations documented as the first entries:
  1. 🟡 Sparflöden (ISK, Lysa, Ella försäkringspengar) go via Räkningar, not direct from Lön as mental model assumes. Zero direct Lön → ISK/Lysa flows in 5+ years of data.
  2. 🔴 Lön used as direct expense account, not just distribution hub: 116 kkr direct to mat (bypassing Matvecka), 19 kkr försäkringspremier, 18 kkr Linneas månadspeng, 15,5 kkr to RKN218 bensinkonto, 13 kkr to "dormant" kök account, direct ICA/HEMKOP groceries on lön's card, and 31 kkr to unknown account 56900725627 (20 tx, recipient unidentified).
  3. 🟡 Petras allowance is sporadic, not monthly as intended.
- Paused the technical work and added new shortterm goal "Konto-modellöversyn" to `__todo.md` capturing the three open decisions: identify 56900725627; renoda lön back to distribution nav or accept-and-document as income+ad-hoc-spend; revisit the broader SEB account structure.

**Significant learnings:**
- Mermaid `flowchart LR` stacks subgraphs vertically in declaration order — moving "Personliga konton" to last in the generator pushed it to the bottom without any positioning hacks.
- Comparing accounts.yaml `intended_behaviours` against actual outgoing-tx descriptions on each account is a cheap and high-value audit. 185 distinct outgoing description patterns on lön surfaced the lön-as-expense-account pattern that's been quietly accumulating for years.
- A `deviations:` block as data (in YAML) beats prose-in-a-report-section. The generator can grow over time, severity badges enable ordering, and each entry's intended/observed/evidence/action_options structure forces the analyst (me) to back claims with specifics.

**Pick up next time:** Decide direction on Konto-modellöversyn — what is 56900725627, renoda lön, or accept-and-document the broad usage. Then either P6 reports (Reserve Funding Ratio, Function/Object pies) or the April budget-net definition gap (+27 181 diary vs +9 181 report.py).

---

## 20260518 — P2-P5 cutover: contracts, multi-split, DuckDB-backed report.py; ECSTER reveal

**Type of work:** coding, debugging, writing
**Repos touched:** ~/financials (account_flows.yaml + recurring_contracts.yaml + DB schema + loaders), aisafe/projects (financial_advisor/CLAUDE.md, pyproject.toml, report.py, __todo.md)

**Session highlights:**
- P2 — Account graph: 18 edges loaded into `account_flow` from `~/financials/account_flows.yaml`. New `load_account_flows.py` + `v_internal_transfer_coverage` view (specificity-ranked match: longest description_pattern wins, null-pattern flows are documentation-only). 294/794 outgoing internal transfers matched on first run (37 %, 2.43 Mkr). Orphans surfaced two structural findings: Lön → Buffer 259 kkr/year and Ella mobil → Lön 253 kkr (the latter validating the roles[] schema premise — account 56990319038 had a former role).
- P3 — Recurring contracts: 21 high-confidence vendors in `~/financials/recurring_contracts.yaml` (6 streaming/subs, telecom, sport, 3 union/A-kassa, månadspeng, 2 health, 4 loans, 3 insurance). New `v_recurring_match` (tightest-drift wins) + `v_contract_anomalies` (expected vs actual per contract). Apply step tagged 496 sub_txs with category + economic_function + object + recurring_id. Anomalies surfaced unprompted: Adobe 17 vs 12 expected (duplicate?), Enkla vardag 24 vs 12 (two policies under one merchant name), HBO Max 8/10 active months.
- Windowing fix: introduced `expected_per_year` override (true count) separate from `expected_months` (broad — months when billing CAN land, for matcher). Anomaly view uses contract's [active_from, active_to] ∩ 12-COMPLETE-month analysis window. Active_from auto-fills from earliest matching tx if not in YAML.
- P4 — Multi-split contracts: caravan loan (4 fixed splits: ränta 602 + admin 45 + amortering 1173 + residual extra) and 3 mortgage tranches (fraction 0.715 ränta + residual amortering, from housing report's aggregate ratio). Loader grew an idempotent reset (delete idx>0 + restore idx=0 amount from `tx.raw`) and multi-split apply (UPDATE idx=0 + INSERT idx 1..N-1 with categorization_history rows). 75 txs split into 144 new sub_tx rows. Integrity green.
- P5 — Cutover: `report.py` lost JSON-load, gained `load_accounts_from_db()` querying `v_tx_sub`. Each sub_tx is a row; multi-split tx appear as 2-4 rows sharing the SHA, balance only on idx=0. accounts.yaml `roles[]` schema bridge via `_account_display_name()`. duckdb added to pyproject.toml + image rebuilt. April 2026 reconciled vs facit with two explainable deltas: −1 550 kr expenses (RKN218 reclass), Klarna ECSTER moved between expense categories.
- Late-day correction: user pointed at the caravan loan invoice screenshot and said "ECSTER is the caravan loan". Data investigation confirmed: ECSTER amounts decline month-over-month (2 170 Sep 2024 → 1 825 Apr 2026 matching invoice 1 820), classic amortizing pattern. Meanwhile 96305773041 had been mistakenly tagged as caravan loan — it's actually a samlings-blankolån (~10 kkr remaining, separate from caravan, with 100 kkr lump on 2025-03-14 being the original consolidation event). Tightened migrate's hardcoded Klarna cleanup to K* KLARNA only; repointed caravan loan contract to ECSTER with declining-amount tolerance and fraction-based ränta split; added new contract for 96305773041. Vehicles.yaml financing block updated; the spurious "user pays 380 kr extra amortering" narrative removed.

**Significant learnings:**
- "Confidence in inferred patterns scales with the breadth of evidence behind them" — the 96305773041 → "Caravan loan" mapping had been confidently propagated through migrate, recurring contract YAML, vehicles.yaml financing block, and even into the housing report's commentary. One sentence from the user dismantled it. Single-column inference at 12 hits is not enough to claim a vendor identity.
- For financed assets, ränta + admin ARE operating cost (price of using money this year) and belong in TCO; only amortering is balance-sheet. Earlier attempts that excluded the entire loan payment from TCO under-reported true cost.
- Mermaid `expected_months` (matcher's gate — broad to absorb bank-day shifts) vs `expected_per_year` (anomaly view's true count) cleanly separates "what's billable" from "how often is billing expected". The Villa+hem quarterly that spreads across 8 candidate months but bills 4 times a year was the use case that forced this split.

**Pick up next time:** Pause and let the foundation settle, OR pick up agentic categorization Batch 1 (historical 2021–2024 consumer credit flows: SEB KORT, SANTANDER, WASA KREDIT, EUROCARD), OR investigate the 56900725627 mystery account.

---

## 20260516 — DuckDB P1: sub_tx + recurring + account_flow tables; accounts.yaml roles[] schema; Lysa accounts

**Type of work:** coding, writing
**Repos touched:** ~/financials (accounts.yaml + db/* + transactions.duckdb), aisafe/projects (financial_advisor/CLAUDE.md)

**Session highlights:**
- Added Lysa as first-class account namespace in `accounts.yaml` — new top-level `lysa:` block keyed by Lysa UUIDs (no SEB account numbers). Four accounts: Lysakonto, Sparkonto, Bred (closed), Ella Försäkringspengar 2024-12-20. Iterated through two Lysa exports — Lysakonto 2 got consolidated into Lysakonto and "Renoveringsfond Frönäs 5:9" (1 kr seed, 2026-05-16) appeared, matching the housing report's previously-mysterious "Lysakonto 3" reference. Cross-reference noted in YAML header comment.
- Introduced `roles[]` time-bounded schema for household accounts. Motivation: SEB caps account count, so the same account number gets repurposed over years (e.g., account 56990319038 was potentially a project earmark before its current "Ella mobil — dormant" role). All 17 household accounts migrated to single-element `roles[]` lists with `from: null, to: null`. New `_account_display_name()` helper handles both shapes (legacy flat for external/lysa, role-based for household).
- P1 schema rewrite in DuckDB: `tx` (immutable bank obs, unique sha PK), `sub_tx` (≥1 per tx, the classification carrier), `recurring` (cashflow contracts), `account_flow` (graph edges), `categorization_history` (audit at sub_tx level). The double-entry invariant `SUM(sub_tx.amount) = tx.amount` is enforced via `v_split_integrity` view.
- SHA uniqueness fix: hash input now includes `occurrence_within_group` (0, 1, 2... for same-content rows within an import). Re-importing the same export is now an idempotent no-op (PK enforces it). The 259 historical SEB collisions (back-to-back same-amount transfers) get distinct hashes that stay stable across re-imports.
- Migration ran clean: 10 678 tx → 10 678 sub_tx (1:1 baseline), zero integrity violations. Two known cleanups (ECSTER+K\* KLARNA → Klarna repayment, BENSIN/AVGIFT RÄKAN → Internal transfers) re-applied at sub_tx level. Note: the ECSTER half of the Klarna cleanup turned out to be wrong (corrected on 2026-05-18 — ECSTER is the caravan loan).
- `transaction_db.py` + `workbench.py` rewritten to operate on sub_tx via `v_tx_sub` joined view. `wb reclassify` takes `--field` (category | economic_function | object | recurring_id). `wb integrity` checks the double-entry invariant.

**Significant learnings:**
- SEB exports contain ~2.5 % true SHA collisions because two same-day same-amount same-account-and-description back-to-back transfers hash identically with `sha256("{date}|{account}|{description}|{amount}")`. The fix preserves the 8-char SHA convention by adding occurrence-within-group as a hash input. Idempotent re-imports drop out for free.
- Separation of observation (tx) from interpretation (sub_tx) lets the model handle bundled payments without losing fidelity. A 2 200 kr loan tx becomes one row in tx (immutable bank fact) and four rows in sub_tx (ränta + admin + amortering schedule + extra), each with its own category/function/object tags, summing to 2 200.
- The `roles[]` schema for accounts.yaml turned out to be exactly what was needed — the next day's orphan-flow analysis surfaced a 253 kkr Ella mobil → Lön historical pattern that strongly hints the account had a former role. Without `roles[]` there would have been nowhere to express that.

**Pick up next time:** P2 — populate `account_flow` from accounts.yaml prose so internal-transfer auto-classification has documented structure to lean on.

---

## 20260515c — Lifestyle report + DuckDB cutover

**Type of work:** coding, writing, devops, research
**Repos touched:** ~/financials (lifestyle report, data/db/ DuckDB store, scripts), aisafe/projects (diary, __todo.md, financial_advisor/CLAUDE.md)

**Session highlights:**
- Wrote `~/financials/lifestyle-financial-reality-report-2026.sv.md` — 10 sektioner covering all five non-asset buckets in one consolidated report (recurring services, food, allowances, healthcare/pets, one-offs + insurance reconciliation + loans recap + total household reality). Includes three new PNG charts (lifestyle_pie, recurring_services_pie, food_trend_2026)
- `generate_lifestyle_charts.py` added alongside vehicle/house generators
- Identified data quality blockers: 484 278 kr Uncategorized/12 mo, ECSTER+K*KLARNA mislabeled as Online shopping, RKN218 category routing bug, Insurance allocation gap (~18 220 kr/yr unattributed between cars/house/caravan)
- Designed and built DuckDB transaction store at `~/financials/data/db/`: schema.sql (tx + category_rules + categorization_history + improvements + 3 views), migrate_from_json.py importer, transaction_db.py helper module, workbench.py CLI, wb Docker wrapper
- Migrated all 10 678 transactions (2021-05-10 → 2026-05-08) into transactions.duckdb
- Applied first two cleanups through the new workbench end-to-end: ECSTER+K*KLARNA→`Klarna repayment` (64 txs, rule klarna-2026-05-15) and RKN218→Internal transfers (20 txs, rule rkn218-route-2026-05-15) — 84 audit rows in categorization_history
- Installed DuckDB CLI locally at `~/.local/bin/duckdb` (single binary install) for ad-hoc reads
- Updated financial_advisor/CLAUDE.md with new DuckDB store section: re-seed command, workbench reference, reclassification convention

**Significant learnings:**
- DuckDB beat the alternatives for this workload: file-based like JSON, SQL for analytics, JSON column type for raw row preservation, atomic UPDATEs for bulk reclassification. "Document database" was the user's framing but the workload (group-by-month, bulk reclass, multi-report reads) is analytical-first
- SEB exports contain ~2.5 % true SHA collisions — same date/account/desc/amount transactions are legitimate (back-to-back transfers) but indistinguishable to `sha256("{date}|{account}|{desc}|{amount}")`. Fix: keep SHA as non-unique human reference, add `pk` auto-increment as real primary key. Preserves the "every row has an 8-char SHA" convention without lying about uniqueness
- Docker user mapping (`-u $(id -u):$(id -g) ... -e HOME=/tmp`) is required when DuckDB files need to be readable by the host. Without it, the file is root-owned and `~/.local/bin/duckdb` gets EACCES
- The reclassify workflow needs three things to be safe: parameterized WHERE, atomic UPDATE+history-write transaction, and a `--dry-run` mode. Workbench has all three; manual SQL UPDATEs would skip the audit row
- "Document database" framing collapses two distinct needs: easy reads (JSON-like) and good queries/updates (relational). DuckDB satisfies both because JSON columns are first-class

**Pick up next time:** Start agentic categorization Batch 1 — historical 2021–2024 consumer credit flows (SEB KORT 540k, SANTANDER 199k, WASA KREDIT 105k, EUROCARD 97k). Decide whether to use `Loan payments` or a new `Credit card repayment` category. Target: Uncategorized < 100 000 kr/12 mo after all batches

---

## 20260515b — KBH30Y caravan onboarded into fleet model

**Type of work:** coding, writing, research
**Repos touched:** aisafe/projects (diary, __todo.md), ~/financials (vehicles.yaml, vehicles_report_2026.md, generate_vehicle_charts.py, charts/)

**Session highlights:**
- Added KBH30Y (Adria Altea 502 UL, 2020) as new `caravans:` top-level block in vehicles.yaml — sibling of `vehicles:` so existing car-only iteration keeps working
- Pulled base specs from car.info (model/year/owners/besiktning history) and Blocket comps (2021 Altea 502 UL at 219 900–249 000 kr → 220 000 kr current_market_value for 2020)
- Replaced indikativa estimates with confirmed numbers from four screenshot images: Folksam insurance 2 524 kr/yr quarterly, loan avtal 645300540675 at 4,7 % with 153 723 kr / 130 mån remaining, June 2026 invoice breakdown 1 820 kr scheduled vs 2 200 kr actual (380 kr/mo extra amortering)
- Reframed loan in TCO: ränta + admin (~647 kr/mo) operating cost in TCO; amortering (~1 553 kr/mo with extra) balance-sheet, excluded
- Storage = egen tomt (0 kr/mo) — final TCO 36 864 kr/yr, monthly set-aside 3 072 kr
- Extended generate_vehicle_charts.py: TCO/MONTHLY_RECURRING/FUND/body_type-aware burnup all caravan-capable; refactored main() into render_asset() helper iterating cars + caravans; per-10km fleet chart kept cars-only (no km basis for caravan)
- Generated kbh30y_ledger / kbh30y_tco / kbh30y_burnup PNGs (teal #1ABC9C distinguishes caravan from cars), embedded in report

**Significant learnings:**
- Caravans depreciate slower than cars — Adria Altea 502 UL 2020 still at ~220 000 kr after 6 years; residual at 2032 (12 yr) realistically 150 000 kr, not 50 000 kr. That alone dropped Ersättningsreserv from 2 564 to 1 923 kr/mo
- For financed assets, ränta + admin belong in TCO (real operating cost = price of using money this year); only amortering is balance-sheet. Earlier draft incorrectly pulled the full loan payment out of TCO and underreported true cost
- Slopad fordonsskatt 2026-02-01 (riksdagsbeslut, släp 751–3 000 kg) saves ~360 kr/yr — small but worth flagging in flottlarm as a positive green row
- At 2032 byte: ~32 600 kr loan remaining vs ~150 000 kr residual = ~117 400 kr net down payment for next caravan — falls out of the model automatically once interest is split from amortization

**Pick up next time:** House report — last asset in M2-Step1. Then resolve the April budget-net definition gap (+27 181 diary vs +9 181 report.py) before running /budget reconcile 2026-05

---

## 20260515 — Swedish reports, pipeline hardening, financial correctness pass

**Type of work:** coding, debugging, writing
**Repos touched:** aisafe/projects, aisafe/skills

**Session highlights:**
- Ran three parallel review agents (financial correctness, technical patterns, readability) across financial_advisor and ~/financials; actioned all findings in one pass
- Added Swedish translation layer to report.py (CATEGORY_SV / THEME_SV / MONTH_SV dicts); all headings, columns, and month references now render in Swedish
- Fixed SHA hash instability in extract.py: added _normalize_date() so xlsx datetime objects and PDF string dates produce identical hashes
- Added income-zero fail-fast discrepancy to report.py; parking folded into MONTHLY_RECURRING to close ledger vs. vehicle-report gap
- Added fleet cost-per-10km chart and <2% TCO slice grouping to generate_vehicle_charts.py

**Significant learnings:**
- When two data sources for the same account produce different hashes, the culprit is almost always date serialization — datetimes from openpyxl serialize differently than strings from pdftotext
- Adding a cost to both the recurring total and the deposit in a ledger table is zero-sum: saldo rows don't shift, only the split between expense and savings changes

**Pick up next time:** May 2026 reconciliation — salary import is missing (income-zero fires); verify MAT annotation date-boundary works correctly for lön account

---

## 20260514 — Vehicle financial reality report: fleet model + burnup charts

**Type of work:** coding, planning, research
**Repos touched:** aisafe/skills, aisafe/projects (financials)

**Session highlights:**
- Built complete vehicle financial reality report for RKN218, PTJ029, MSA52U — per-car TCO, ledger, and burnup charts
- Committed to fleet cost model exclusively: removed Avskrivning from all TCO tables, keeping only Ersättningsreserv (monthly accrual toward replacement)
- All three cars given unified 2032 replacement target (fleet strategy review); Ersättningsreserv amounts recalculated over 78 months (Jun 2026 → Dec 2032)
- Generated 3 per-vehicle burnup charts showing cumulative savings trajectory with milestone markers
- Compressed session:end context gathering from ~10 individual tool calls into one batch script (`gather.sh`)
- Built `/budget car` skill (budget:subagents:car) for per-vehicle financial reality reporting

**Significant learnings:**
- "True-cost deposit" = total_annual_costs / 12, where total includes all recurring (fuel, accrual, tire reserve, km-based service) — not just scheduled YAML bills; this ensures the deposit actually covers reality
- Fleet model and consumer TCO double-count capital costs if both Avskrivning and Ersättningsreserv are present — must pick one; fleet model chosen for predictable planning
- Burnup charts must anchor to the fund start date (not the odometer reading date) or milestone dates come out wrong

**Pick up next time:** Update vehicles.yaml monthly_set_aside values (PTJ029: 4,038 kr, MSA52U: 5,728 kr — still shows 0); open the three replacement savings accounts and start funding them

---

## 20260510b — /budget skill: reconcile phase built and dry-run against April facit

**Type of work:** coding, planning, research
**Repos touched:** aisafe/skills

**Session highlights:**
- Designed four-phase /budget skill (capture, categorize, reconcile, report); built reconcile phase first as it gates May 2026 close
- Moved standalone /reconcile skill into budget tree (budget:subagents:reconcile); frozen April report + inputs as facit at ~/financials/facit/2026-04/ for regression testing
- Dry-ran /budget reconcile 2026-04: discrepancy walk matched facit (clean); identity check ✗ — both the two-term formula and the pairing-based three-term formula fail to reproduce April's diary calibration numbers (+1 319 / +27 181 / 25 862)
- Root cause partly traced: pairing via build_transfer_pairs is mandatory for leakage (SEB shows sender names on incoming legs, not account numbers); budget-net gap of 18 000 kr vs report.py Overview Net is definitional and unresolved

**Significant learnings:**
- The reconciliation calibration step worked exactly as designed: it caught a wrong formula instead of silently declaring closure — this is the correct behavior for a diagnostic identity check
- `build_transfer_pairs` in report.py is load-bearing for leakage classification: never classify transfer legs independently on SEB data because incoming legs carry personal names, not account numbers
- The diary's "budget net" (+27 181) differs from report.py's Overview Net (+9 181) by 18 000 kr — the legacy formula that produced the diary number has not been recovered in code and is an open issue before May 2026 reconciliation can be trusted

**Pick up next time:** Recover the budget-net definition gap (18 000 kr) before running /budget reconcile for May 2026 — likely requires re-running the legacy scratch computation used during the April close

---

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
