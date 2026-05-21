# Financial Advisor

## Project purpose

A monthly household budget reporting tool for a two-person household. Raw SEB bank exports (Excel + PDF) are fed into a three-stage Docker pipeline that extracts transactions, categorizes them against a persistent rule set, and produces a Markdown + Mermaid report. The goal is to build lasting financial habits through honest monthly budgets, discrepancy detection, and a living improvement checklist.

## Usage

```bash
# Full pipeline (P5+ — report.py reads DuckDB, not JSON)
make extract      # parse all xlsx/pdf in ~/financials/data/ → transactions.json
make categorize   # apply rules + annotations → categorized_transactions.json
# DB pipeline — seed DuckDB and apply contracts/flows before reporting:
docker run --rm -u $(id -u):$(id -g) -v "$HOME/financials:/data" \
  -v /tmp:/tmp -e HOME=/tmp python:3.12-slim \
  sh -c "pip install --user duckdb pyyaml -q && \
         python /data/data/db/migrate_from_json.py --reset-rules && \
         python /data/data/db/load_account_flows.py && \
         python /data/data/db/load_recurring_contracts.py --apply"
make report                    # generate YYYY-MM_budget.md (defaults to last complete month)
make report MONTH=2026-05      # specific month

# If only the DB changed (workbench reclassifications, new contracts):
make report                    # report reads DB directly
```

All Docker runs use `--network=none`. The financials directory is mounted as `/reports/` inside the container; host paths like `~/financials/foo.json` become `/reports/foo.json` in code.

## Stack

- **Python** — extract.py, categorize.py, report.py
- **Docker** — `financial-advisor:latest`, network-isolated at runtime
- **openpyxl** — Excel parsing
- **pdftotext -layout** — PDF parsing (poppler)
- **Mermaid** — embedded in Markdown for pie charts
- Rebuild image after any source change: `make build`

## File layout

```
~/financials/
  data/                        # raw SEB exports (xlsx + pdf) — input
    db/                        # DuckDB store (NEW — 2026-05-15)
      transactions.duckdb      # canonical working store; queryable & updatable
      schema.sql               # table/view definitions (versioned)
      migrate_from_json.py     # one-shot JSON → DuckDB importer (re-runnable)
      transaction_db.py        # Python helper module: TransactionDB class
      workbench.py             # CLI: uncategorized | find | reclassify | history | sql | summary
      wb                       # Docker wrapper for workbench (host-friendly)
  transactions.json            # output of make extract (raw input)
  categorized_transactions.json # snapshot input for migration; legacy report.py still reads this
  categories.json              # master config (rules, limits, flow rules, improvements)
  annotations.json             # exact-match transaction overrides
  accounts.yaml                # account model: household vs external sections, swish_alias, descriptions, intended behaviours, expected deviations
  discrepancy_log.md           # human explanation for each discrepancy exception
  RULES.md                     # account structure, flow rules, rule engine docs (private)
  YYYY-MM_budget.md            # generated monthly reports

~/repos/aisafe/projects/financial_advisor/
  src/financial_advisor/
    extract.py                 # SEB xlsx + pdf → transactions.json
    categorize.py              # rules + annotations → categorized_transactions.json
    report.py                  # categorized data → Markdown report (currently reads JSON; DuckDB cutover pending)
  Makefile
  CLAUDE.md                    # this file
  # RULES.md lives in ~/financials/ (private, not in repo)
```

### DuckDB store — `~/financials/data/db/` (schema v2, P1 — 2026-05-16)

The DuckDB store is the **live, queryable working copy** of transactions. The
JSON pipeline still produces `categorized_transactions.json`, which seeds the
DB via `migrate_from_json.py`. Until `categorize.py` and `report.py` are
cut over to read DuckDB directly, treat the DB as the source of truth for
ad-hoc queries, bulk reclassifications, and exploratory categorization — and
re-seed it whenever the JSON pipeline runs.

**P1 architecture — separation of observation from interpretation:**

- **`tx`** is the immutable bank observation. `sha` is the PRIMARY KEY and is
  **unique** (occurrence-within-group is part of the hash input, so re-importing
  the same export is an idempotent no-op and true SEB duplicates get distinct
  hashes). Columns: `sha`, `date`, `account`, `description`, `merchant`, `amount`,
  `balance`, `source_file`, `raw`, `status`, `annotation_reason`. **No category
  on tx** — classification lives on sub_tx.
- **`sub_tx`** is the classification carrier. Every tx has **≥1** sub_tx; simple
  cases are 1:1; bundled payments (loan = interest + amortization + admin;
  bundled insurance covering multiple assets) split into N sub_tx. Columns:
  `id`, `tx_sha`, `idx`, `amount`, `category`, `economic_function`, `object`,
  `recurring_id`, `rule_applied`, `annotated_at`, `notes`.
- **Double-entry invariant:** `SUM(sub_tx.amount WHERE tx_sha = X) = tx.amount`
  for every X. View `v_split_integrity` returns violators (must be empty).
- **`recurring`** is the expected-cashflow contract table: `vendor_pattern`,
  `amount_expected` (signed), `amount_tolerance_pct`, `expected_months INT[]`
  (e.g. [1,4,7,10] for quarterly), `years_between` (1 default; 2 for biennial),
  `splits` (JSON list of {function, object, amount_or_fraction, category}),
  `active_from`/`active_to`, `status`, `last_fulfilled_date`, `next_due_date`.
  Sub_tx that fulfill a contract reference it via `sub_tx.recurring_id`.
- **`account_flow`** captures the household account graph as data: edges with
  `from_account`, `to_account`, `description_pattern`, `typical_amount`,
  `expected_months[]`, `purpose`. Drives automatic classification of internal
  transfers (P2).

**Auxiliary tables:** `category_rules` (extended with `economic_function` and
`object` columns); `categorization_history` (one row per sub_tx field change
with `field`/`previous_value`/`new_value`/`rule_applied`/`reason`);
`improvements`.

**Views:** `v_tx_sub` (the canonical tx ⨝ sub_tx join), `v_split_integrity`
(double-entry check), `v_monthly_category`, `v_uncategorized_top`,
`v_recurring_merchants`.

**Object values** (P1): `house`, `rkn218`, `ptj029`, `msa52u`, `kbh30y`, or
`NULL`. Reserved for tangible assets only — allowances, services, food, and
all other non-asset costs keep `object=NULL` and carry classification via
`category` + `economic_function`.

**Economic function values** (P1): `lifestyle_consumption`, `asset_preservation`,
`debt_cost`, `debt_reduction`, `resilience_building`, `wealth_building`,
`leakage`. Not yet populated (all NULL in P1 baseline); the auto-classifier in
P2 + recurring-contract assignment in P3 fill it.

### Account graph — `account_flow` (P2 — 2026-05-18)

The household pipeline (which tracked account feeds which, with what description
and typical amount) is captured as data in `account_flow`. Source of truth is
`~/financials/account_flows.yaml`; loaded into the DB via
`load_account_flows.py`. 18 edges currently documented across purposes
`household-pipeline` / `allowance` / `savings` / `reimbursement` /
`liquidity-borrow` / `liquidity-repayment` / `fund-purchase`.

**Matching rules:**
- `account_flow.from_account` is the canonical 11-digit SEB key (no spaces, no
  label). `tx.account` is the human-readable label. The matching view derives
  the key via `regexp_replace(tx.account, '[^0-9]', '', 'g')`.
- Only flows with a **non-null** `description_pattern` participate in
  auto-matching. Null-pattern edges (sparse / ad-hoc flows where there's no
  reliable description signal) live in the table for documentation but never
  auto-match — they appear in `v_account_flow_documented` only.
- When multiple flows could match a single sub_tx, the **longest** description
  pattern wins (most specific).
- `active_from` / `active_to` bound the edge to a time window (e.g. MAT routing
  moved from räkningar to lön on 2026-05-01 — two edges with complementary
  date bounds capture both regimes).

**Views:**
- `v_internal_transfer_coverage` — per outgoing internal-transfer sub_tx, the
  matched flow (or NULL if orphan). Use this to spot which transfers map onto
  a known edge and which don't.
- `v_account_flow_documented` — edges that exist for documentation but never
  auto-match (null pattern or non-active status).

**Workbench command:**
```bash
./wb flow-coverage              # match-rate summary + per-edge breakdown
./wb flow-coverage --orphans    # top orphan (account, description) clusters
```

**Adding / removing edges:** edit `~/financials/account_flows.yaml`, then re-run
`load_account_flows.py` (it wipes and reloads `account_flow` from the YAML, so
removing a YAML entry deletes the row from the table).

### Recurring contracts — `recurring` (P3 — 2026-05-18)

Expected vendor cashflows are captured as data in `recurring`. Source of
truth is `~/financials/recurring_contracts.yaml`; loaded into the DB via
`load_recurring_contracts.py` (run with `--apply` to also tag matched
sub_txs with category / economic_function / object / recurring_id from
each contract's splits).

**Schema fields:** `vendor_pattern` (LIKE on `tx.merchant`),
`amount_expected` (signed), `amount_tolerance_pct`, `expected_months INT[]`
(months when billing CAN land — broad for matcher), `expected_per_year`
(optional override of the true count per cycle; null defaults to
`len(expected_months)`), `years_between` (1 default; 2 for biennial),
`splits` (JSON list of `{category, economic_function, object, [notes]}`),
`active_from` / `active_to`, `status`, `notes`.

**Active window semantics — every contract has explicit dates:**
- `active_from` — the contract's start date. If omitted from YAML, the
  loader auto-fills it with the earliest `tx.date` where `merchant LIKE
  vendor_pattern`. Override in YAML when you know the actual start.
- `active_to` — `NULL` means "still ongoing". Set explicitly to a date when
  the contract is cancelled or paused.
- The anomaly view uses the **intersection** of the rolling 12-month
  analysis window with `[active_from, active_to]` as the effective window.
  Contracts that started mid-window get a proportionally smaller expected
  count — no false "missing" alarms from data starting later than the
  contract.

**`expected_months` vs `expected_per_year`:**
- `expected_months` is **what the matcher gates on** — a tx whose
  `extract(month FROM date)` is not in this list won't match. Set this
  broad enough to absorb bank-day shifts (e.g. a quarterly bill that
  sometimes lands on the last day of one month, sometimes the first of the
  next — list both).
- `expected_per_year` is **what the anomaly view counts as the true
  expected fulfillment count** per year. For Villa+hem quarterly the
  matcher uses `[3,4,6,7,9,10,12,1]` (8 months) but `expected_per_year=4`
  (4 quarterly bills regardless of which adjacent month catches each one).
- If `expected_per_year` is null the view defaults to
  `len(expected_months)` — correct for cleanly monthly/quarterly contracts.

**Splits semantics:**
- A contract's `splits` is a list. Length 1 is the simple case (single
  classification for the whole sub_tx); length ≥ 2 splits one tx into
  multiple sub_tx with separate classifications.
- Each split entry carries `category` / `economic_function` / `object` /
  optional `notes`, and exactly one of:
  - `amount: <fixed signed amount>` (e.g. `-602` for the caravan loan's
    ränta component)
  - `fraction: <0..1>` (e.g. `0.715` for mortgage ränta share)
  - `residual: true` — gets whatever's left after fixed/fraction allocations.
    At most one residual entry per contract.
- The loader's apply step:
  - **Single-split (length 1)**: UPDATE sub_tx idx=0 with the classification.
  - **Multi-split (length N ≥ 2)**: compute per-split amounts; verify they
    sum to tx.amount within 0.01 kr; UPDATE idx=0 with split[0]; INSERT
    new sub_tx for idx 1..N-1 with split[1..]. Every change writes a
    `categorization_history` row (field='split').
  - Re-running `--apply` first resets any previously-contract-applied
    sub_tx back to the 1:1 baseline (deletes idx>0, restores idx=0
    amount=tx.amount and category from `tx.raw`), then re-applies. Safe
    to run repeatedly.

**Matching rules:**
- `tx.merchant LIKE r.vendor_pattern`
- `|tx.amount - r.amount_expected| / |r.amount_expected| <= tolerance_pct / 100`
- `extract(month FROM tx.date)` is in `r.expected_months`
- `tx.date` within `[r.active_from, r.active_to]` if set
- When multiple contracts match a single sub_tx, the **smallest drift_pct** wins.

**Views:**
- `v_recurring_match` — per sub_tx, the best-matching contract with `drift_pct`.
- `v_contract_anomalies` — per active contract, last-12-month expected vs
  actual count, average and max drift, traffic-light status (✅ on track /
  🟡 fewer than expected / 🟡 more than expected / 🟡 amount drift / 🔴 no matches).

**Workbench commands:**
```bash
./wb contracts                # list contracts with vendor/expected/match counts
./wb contract-anomalies       # expected vs actual per contract (12 mo)
./wb tx-detail <sha>          # show all sub_tx for a tx (verify splits)
```

**Adding / changing contracts:** edit `~/financials/recurring_contracts.yaml`,
then re-run `load_recurring_contracts.py --apply`. The loader wipes and
reloads contracts, clears any orphan `recurring_id` references on sub_tx
first, then re-applies splits. Safe to re-run.

**Re-seed from JSON:**
```bash
docker run --rm -u $(id -u):$(id -g) -v "$HOME/financials:/data" \
  -v /tmp:/tmp -e HOME=/tmp python:3.12-slim \
  sh -c "pip install --user duckdb -q && \
         python /data/data/db/migrate_from_json.py"
```

**Common workbench commands** (via `./wb` wrapper or directly through Docker):
```bash
# Top uncategorized merchants
./wb uncategorized --limit 20

# Find sub_tx by merchant LIKE pattern
./wb find 'ECSTER%'

# Preview a bulk reclassification (no writes).
# --where references the joined view aliases: t (tx) and s (sub_tx)
./wb reclassify --where "t.merchant LIKE 'ECSTER%'" \
                --field category \
                --new-value 'Klarna repayment' \
                --rule 'klarna-2026-05-15' \
                --reason 'Klarna amortering — not new shopping' \
                --dry-run

# Apply the reclassification (writes UPDATE on sub_tx + categorization_history)
./wb reclassify --where "t.merchant LIKE 'ECSTER%'" \
                --field category \
                --new-value 'Klarna repayment' \
                --rule 'klarna-2026-05-15' \
                --reason 'Klarna amortering — not new shopping'

# Update a different sub_tx field
./wb reclassify --where "t.merchant = 'TELIA SVERIGE'" \
                --field economic_function \
                --new-value 'lifestyle_consumption' \
                --rule 'telia-fn-2026-05-16' \
                --reason 'Telecom is current consumption'

# Show audit history
./wb history --rule klarna-2026-05-15
./wb history --sha b544ad60

# Arbitrary SQL (read-only)
./wb sql "SELECT category, SUM(-sub_amount) FROM v_tx_sub WHERE date >= '2026-04-01' GROUP BY 1"

# Double-entry integrity check
./wb integrity

# Local DuckDB CLI (installed at ~/.local/bin/duckdb) — read-only ad-hoc
duckdb ~/financials/data/db/transactions.duckdb -c "SELECT * FROM v_uncategorized_top LIMIT 10"
```

**Reclassification convention:** every bulk update goes through
`wb reclassify` or `TransactionDB.reclassify()`. Specify `--field` (one of
`category`, `economic_function`, `object`, `recurring_id`). Both write one
`categorization_history` row per affected sub_tx with `field`,
`previous_value`, `new_value`, `rule_applied`, and `reason`. Treat
`annotations.json` for narrow single-tx overrides the rule engine should
respect at categorize-time; use the DB for everything bulk and post-hoc.

## Report language

Report output is **Swedish**. All section headings, table column names, month names, and category/theme labels render in Swedish. The data layer (JSON keys, Python variables, category names in rules) remains English. Translation lives in `report.py`: `CATEGORY_SV`, `THEME_SV`, `MONTH_SV` dicts; `sv_cat()`, `sv_theme()`, `sv_month()` helpers.

## Report data source (P5 — cutover 2026-05-18)

`report.py` reads from the DuckDB store at `/reports/data/db/transactions.duckdb`,
not from `categorized_transactions.json`. The JSON pipeline (`make extract`,
`make categorize`) still produces the JSON, which then seeds the DB via
`migrate_from_json.py`. After P5:

- Each `sub_tx` is one row in the report. Unsplit tx are 1:1 with the
  legacy JSON pipeline; multi-split tx (mortgage interest + amortization,
  caravan loan ränta + admin + amortering + extra) appear as 2–4 rows
  sharing the same SHA. The amounts sum to `tx.amount` per SHA (enforced
  by `v_split_integrity`).
- The `Konto` (full bank statement) section shows balance only on idx=0 of
  a split; subsequent split rows leave balance blank to avoid implying
  separate balances per component.
- Aggregates (Översikt, per tema, per kategori) sum `sub_tx.amount` —
  totals stay correct.
- April 2026 facit reconciles with two explainable differences vs the
  legacy JSON pipeline output:
  - **Expenses −1 550 kr** (RKN218 reclassification: BENSIN RÄKAN 800 +
    AVGIFT RÄKAN 750 moved from a bogus "RKN218" expense category to
    Internal transfers — they were always internal pipeline transfers).
  - **Klarna ECSTER −1 825 kr** moved from Online shopping to Klarna
    repayment within the expense buckets — total expenses unchanged.

`accounts.yaml` lookup: `report.py` now reads household entries via the
P2 `roles[]` schema (using the newest role's `name` for display) and
external/lysa entries via the legacy flat `name` field.

## Report sections (in order)

1. **Avvikelser** — flow rule violations, monthly limit overruns, uncategorized transactions; income-zero fail-fast fires here if total_income == 0
2. **Förbättringar** — checkbox action list driven by `categories.json`, wrapped in `<details>`
3. **Översikt** — income / expenses / net + reconciliation row: Netto (budget) + Överföringsläckage = Förändring spårade konton
4. **Utgifter per tema** — top-5 table + Mermaid pie
5. **Utgifter per kategori** — Mermaid pie + table
6. **Kategoriöversikt** — full table with % share
7. **Inkomster**
8. **Per konto** — summary per account with category split
9. **Alla transaktioner — datum** — all budget transactions chronologically
10. **Konton** — full bank statement per account (with running balance + SHA ID)
11. **Alla transaktioner — tema** — grouped, sorted by merchant then date, wrapped in `<details>`
12. **Alla transaktioner — kategori** — grouped, sorted by merchant then date, wrapped in `<details>`
13. **Överföringar** — internal/family/swish transfers excluded from budget, with Source → Destination columns and Documentation links

## Transaction IDs

Each transaction is SHA256-hashed from `"{date}|{account}|{description}|{amount}"`, truncated to 8 hex chars. IDs are stable across re-runs and used as keys in annotations, discrepancy exceptions, and improvements.

**Always cite the 8-char ID when referring to any specific transaction** — in tables, in prose, in commit messages, anywhere. A statement like "the 4 000 kr loan repayment" is not actionable; "`cabf4721` (4 000 kr loan repayment)" is. This applies in both directions: include the ID in every transaction row of every report or ad-hoc table, and reference the ID inline when discussing a transaction in conversation.

## SEB data quirks

- Outgoing transfers: description field contains the **destination account number** — resolved to a display name via `accounts.json`
- Incoming transfers: description field contains the **sender's name** (e.g. `PERSON A`, `PERSON B`) — NOT the account name
- Consequence: transfers from a shared account appear on receiving accounts with the account holder's personal name
- Date suffix `/YY-MM-DD` appended by SEB to truncated merchant names — stripped before categorization
- PDF exports: stop parsing at "Reserverade belopp" (pending/unbooked transactions)

## Milestones

- **M1** ✓ Last month's expenses as a categorized budget report
- **M2** 12-month expense forecast — fixed monthly set-aside for irregular bills
- **M3** Asset budgets for vehicles, property, and recreational equipment with savings burnup charts
- **M4** Monthly traffic-light summary + intended-vs-actual comparison
