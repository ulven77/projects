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
  transactions.json            # output of make extract
  categorized_transactions.json # output of make categorize
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
    report.py                  # categorized data → Markdown report
  Makefile
  CLAUDE.md                    # this file
  # RULES.md lives in ~/financials/ (private, not in repo)
```

## Report sections (in order)

1. **Discrepancies** — flow rule violations, monthly limit overruns, uncategorized transactions
2. **Improvements** — checkbox action list driven by `categories.json`
3. **Overview** — income / expenses / net
4. **Expenses by theme** — Mermaid pie + table
5. **Expenses by category** — Mermaid pie + table
6. **Category breakdown** — full table with % share
7. **Income breakdown**
8. **Per account** — summary per account with category split
9. **All transactions — by date** — all budget transactions chronologically
10. **Accounts** — full bank statement per account (with running balance + SHA ID)
11. **All transactions — by theme** — grouped, sorted by merchant then date
12. **All transactions — by category** — grouped, sorted by merchant then date
13. **Transfers** — internal/family/swish transfers excluded from budget, with Source → Destination columns and Documentation links

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
