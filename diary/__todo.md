## Current goal (Max 1)
### Financial Advisor: 12-month expense forecast (M2)
Fixed monthly set-aside amounts for irregular bills, so the household can see what to save each month to cover annual/quarterly costs without surprises.

**Step 1 — Action the improvements list**
- Cancel STYRKEFABRIK, Adobe, Nextory, Allente subscriptions
- Move Amazon Prime payment to Gemensamt räkningar
- Move Klarna payments to Gemensamt räkningar
- Identify 10× APPLE COM/BI charges and recategorize correctly
- Understand 2× SAN FRANCISC charges
- Create Assets and Expenses report report
    - Purpose of report is to follow-up spending on the big expenses by asset and expense type.
        - Assets
            - Cars (skills/commands/budget/assets/vehicle-financial-reality-metrics.md)
                - RKN 218 (Volvo S80 / Car)
                - PTJ 029 (Toyota Avensis / Car)
                - MSA 52U (Kia E-soul / Car)
            - Caravan (See /home/uven/repos/aisafe/skills/commands/budget/assets/camper-financial-reality-metrics)
                - 
            - House (see [text](../../skills/commands/budget/assets/housing-financial-reality-metrics.md))
                - 
        - Liabilities 
            - Loans without collateral (see /home/uven/repos/aisafe/skills/commands/budget/assets/Unsecured Loan Financial Reality Metrics.md)
        - Non-Assett/Loan related recurring costs (Basically quality of life services)
            - All recurring, periodic and known irregular costs not connected to major assets
            - Were we have little say in how much they are other than adjusting recurring costs.
        - Food/consumption
            Everything
        - Allowanses / person related costs.

**Step 2 — Reconcile May 2026**
- ⚠ First: recover budget-net definition gap — diary's April budget net (+27 181) is 18 000 kr larger than report.py Overview Net (+9 181). Formula unknown. April facit at ~/financials/facit/2026-04/ for reference.
- First month with the new MAT routing (lön → Matvecka) — verify the new annotation fires correctly
- Use `/budget reconcile 2026-05` (skill is in diagnostic mode until budget-net is resolved)
- Note: Petra's account is permanently external by design — not to be exported

**Step 3 — Build forecast**
- Identify irregular annual/quarterly bills in categorized_transactions.json
- Compute monthly set-aside per category
- Add forecast section to report.py


## Shortterm goals (Max 3)

**Hermes: Categorize transactions and produce reproducible report (Step 4)**
- Define keyword → category rules (HEMKOP → Groceries, TELIA → Telecom, etc.)
- Apply rules during ingestion or as a query layer in DuckDB
- Write BDD feature: "categorize transactions"
- Update notebook: costs grouped by category, per account, rolling 2 months
- Add `make report` target: export notebook to HTML/PDF via `marimo export`

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
_On session start Claude looks at platform engineering, AI sites and the contents of last session and recommends 3 articles to read_

## Active project milestones (Max 3)
- Financial Advisor M1 ✓ — last month expenses as categorized budget
- Financial Advisor M2 — 12-month expense forecast + fixed monthly set-aside
- Hermes — cost control with categorized report
- GoPro Tandådalen movie
