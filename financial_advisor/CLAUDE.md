# Financial Advisor

## Project purpose

A monthly household budget reporting tool for a two-person household. Raw SEB bank exports (Excel + PDF) are fed into a three-stage Docker pipeline that extracts transactions, categorizes them against a persistent rule set, and produces a Markdown + Mermaid report. The goal is to build lasting financial habits through honest monthly budgets, discrepancy detection, and a living improvement checklist.

## Usage

```bash
# Full pipeline
make extract      # parse all xlsx/pdf in ~/financials/data/ → transactions.json
make categorize   # apply rules + annotations → categorized_transactions.json
make report       # generate YYYY-MM_budget.md (defaults to last complete month)
make report MONTH=2026-05   # specific month

# Partial — skip extract if only rules changed
make categorize && make report
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

### DuckDB store — `~/financials/data/db/`

The DuckDB store is the **live, queryable working copy** of transactions. The
JSON pipeline still produces `categorized_transactions.json`, which seeds the
DB via `migrate_from_json.py`. Until `categorize.py` and `report.py` are
cut over (next step), treat the DB as the source of truth for ad-hoc
queries, bulk reclassifications, and exploratory categorization work — and
re-seed it whenever the JSON pipeline runs.

**Schema (tx table):** `pk` (auto-increment PRIMARY KEY) · `sha` (8-char content
hash, NOT unique — SEB exports have ~2.5 % true duplicates) · `date` · `account`
· `description` · `merchant` · `amount` · `balance` · `source_file` · `category`
· `theme` · `raw` (JSON of original row) · `annotated_at` · `annotation_reason`
· `rule_applied`.

**Auxiliary tables:** `category_rules` (priority-ordered, supports date bounds);
`categorization_history` (one row per category change, with rule and reason);
`improvements` (mirror of categories.json improvements list); views
`v_monthly_category`, `v_uncategorized_top`, `v_recurring_merchants`.

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

# Find transactions by merchant LIKE pattern
./wb find 'ECSTER%'

# Preview a bulk reclassification (no writes)
./wb reclassify --where "merchant LIKE 'ECSTER%'" \
                --category 'Klarna repayment' \
                --rule 'klarna-2026-05-15' \
                --reason 'Klarna amortering — not new shopping' \
                --dry-run

# Apply the reclassification (writes UPDATE + categorization_history rows)
./wb reclassify --where "merchant LIKE 'ECSTER%'" \
                --category 'Klarna repayment' \
                --rule 'klarna-2026-05-15' \
                --reason 'Klarna amortering — not new shopping'

# Show audit history for a rule or a specific transaction
./wb history --rule klarna-2026-05-15
./wb history --sha b544ad60

# Arbitrary SQL
./wb sql "SELECT category, SUM(-amount) FROM tx WHERE date >= '2026-04-01' GROUP BY 1"

# Local DuckDB CLI (installed at ~/.local/bin/duckdb) — read-only ad-hoc
duckdb ~/financials/data/db/transactions.duckdb -c "SELECT * FROM v_uncategorized_top LIMIT 10"
```

**Reclassification convention:** every bulk update goes through `wb reclassify`
or `TransactionDB.reclassify()`. Both write one `categorization_history` row
per affected transaction with `previous_category`, `new_category`,
`rule_applied`, and `reason`. This is the auditable replacement for ad-hoc
annotations.json edits — keep `annotations.json` for narrow, single-tx overrides
the rule engine should respect; use the DB for everything bulk.

## Report language

Report output is **Swedish**. All section headings, table column names, month names, and category/theme labels render in Swedish. The data layer (JSON keys, Python variables, category names in rules) remains English. Translation lives in `report.py`: `CATEGORY_SV`, `THEME_SV`, `MONTH_SV` dicts; `sv_cat()`, `sv_theme()`, `sv_month()` helpers.

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
