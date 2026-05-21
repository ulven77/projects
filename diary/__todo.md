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
                - ✓ RKN 218 (Volvo S80 / Car) — vehicles_report_2026.md complete
                - ✓ PTJ 029 (Toyota Avensis / Car) — vehicles_report_2026.md complete
                - ✓ MSA 52U (Kia E-soul / Car) — vehicles_report_2026.md complete
            - Caravan (See /home/uven/repos/aisafe/skills/commands/budget/assets/camper-financial-reality-metrics)
                - ✓ KBH30Y (Adria Altea 502 UL / Husvagn) — caravan section in vehicles_report_2026.md · försäkring (Folksam 2 524 kr/år), lån (153 723 kr kvar @ 4,7 %), marknadsvärde (220 000 kr) och uppställning (egen tomt, 0 kr) bekräftade · återstår: faktiska reparations-/serviceutgifter (CARAVANHALLE/HUSVAGN FIX historik) för bättre underhållsschablon
            - House (see [text](../../skills/commands/budget/assets/housing-financial-reality-metrics.md))
                - ✓ Gnesta Frönäs 5:9 — `~/financials/housing-financial-reality-report-2026.sv.md` (17 sektioner, transaktions­spårbar, mermaid-pajdiagram, stress-tests). AGENT_INSTRUCTIONS.md i `~/financials/data/house/` håller konventioner och handover. Återstår: omsättning bolån 2026-05-28 (akut, risk #6), starta 5 000 kr/mån avsättning till Lysakonto 3, beställ VVS-provtryckning
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

**Konto-modellöversyn — fundera på hur kontona faktiskt används**
Pausad 2026-05-21. Vi hittade tre tydliga avvikelser mellan accounts.yaml `intended_behaviours` och faktisk data:
1. 🟡 Sparflöden (ISK, Lysa, Ella försäkringspengar) går via Gemensamt räkningar, inte direkt från Gemensamt lön som mental modell antar.
2. 🔴 Gemensamt lön används som **direkt utgiftskonto** för många kategorier, inte bara distributionsnav: 116 kkr/år direkt till mat (kringgår Matvecka), 19 kkr försäkringspremier, 18 kkr Linneas månadspeng, 15,5 kkr RKN218-bensinkonto, 13 kkr till gemensamt kök (som ska vara dormant), plus direkta livsmedelsköp på lön-kortet.
3. 🟡 Petras fickpeng är sporadisk (3 utbetalningar senaste 12 mån, ofta i lumps) istället för månadsvis som intentionen säger.

Hela inventeringen finns i `~/financials/account-flow.md` med flowchart + tabeller + avvikelser. Källa: `~/financials/account_flows.yaml`. Pedagogisk version används också för att rita en mental modell.

**Öppna frågor att fundera på:**
- Vad är 56900725627? 20 tx från lön på sammanlagt 31 397 kr/år. Hampus, gammal extern motpart, eller annat? (Också flaggat under Agentic categorization Batch 2 nedan — fynden är samma konto.)
- **Renoda lön**: flytta direktutgifter (PREMIE FÖRS, ICA-köp på kortet, MÅNADSPENG, RKN218-fond) till räkningar/uffe betalkonto → lön blir bara distributionsnav?
- **Eller acceptera mönstret**: uppdatera accounts.yaml så lön beskrivs som "income + ad-hoc spend" och lägg till de saknade återkommande flödena (lön→mat, lön→MÅNADSPENG, lön→RKN218) i `account_flows.yaml`?
- Skissa om SEB-kontostrukturen mer holistiskt: stämmer rollerna i accounts.yaml fortfarande?

**När detta tas vidare:** beslut → uppdatera accounts.yaml (`intended_behaviours` + `roles[]`-historik om något konto bytt syfte) → uppdatera account_flows.yaml (lägg till saknade flöden eller justera) → kör om generate_account_flow_report.py och v_internal_transfer_coverage för att se täckningen.

**Agentic categorization workflow** (on top of new DuckDB foundation)
Systematic, audited reduction of Uncategorized 426 483 kr/12 mo using the `wb` workbench. Claude works through Uncategorized merchants in batches, proposes patterns, dry-runs, applies — every change leaves a `categorization_history` row.
- Batch 1 — recurring large flows (SEB KORT, SANTANDER, WASA KREDIT, EUROCARD) — historical 2021–2024 consumer credit. Likely `Loan payments` or new `Credit card repayment` category. ~1 000 000 kr cumulative.
- Batch 2 — recurring household transfers (56900725627 — 113 txs, 69 908 kr) — identify recipient (likely family member), route to `Internal transfers` or `Family transfers`.
- Batch 3 — vehicle-related uncategorized (SERV. MSA52U 14 400, BILKÖP 21 000×2, KIA /IF SKADEFÖRSÄKRING 9 073) → `Vehicle costs` or asset-specific.
- Batch 4 — house & solar (MÅLARE LARS AXELSSON 81 300, solceller fakturor) → `Housing` (already in housing report's underhållsskuld).
- Batch 5 — gifts & one-offs (PRESENT ELLA, GULDSMEN, MOPPE LINNEA, RESA, DATOR UFFE) → new `Gifts & one-offs` category vs Entertainment.
- Goal: Uncategorized < 100 000 kr/12 mo for the 12-mo window. Track via `wb summary` before/after.
- Each batch ends with a populated `category_rules` row so re-categorization on new SEB imports is automatic.

**Non-asset recurring services + consumption reports**
✓ `~/financials/lifestyle-financial-reality-report-2026.sv.md` — 10 sektioner: löpande tjänster, mat, fickpeng, hälsovård/husdjur, engångshändelser, försäkringsavstämning, lån, hushållsverklighet. Charts: lifestyle_pie, recurring_services_pie, food_trend (12 mån). Inga osäkrade lån identifierade. Skript: `generate_lifestyle_charts.py`.
- ✓ Klarna/Ecster 37 900 kr reklassificerad → `Klarna repayment` (64 txs, rule `klarna-2026-05-15`)
- ✓ RKN218 bogus category → `Internal transfers` (20 txs, rule `rkn218-route-2026-05-15`)
- ⚠ Identifiera 10× APPLE COM/BI per månad (App Store/iCloud/Apple One mix)
- ⚠ Verifiera försäkringsallokering — PREMIE FÖRS. 22 178 kr och Trygg-Hansa 8 808 kr/år behöver mappning mot asset-rapporter
- Säker årsbesparing från report §9: ~18 475 kr/år (Adobe + Storytel + Allente + STYRKEFABRIK)

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
