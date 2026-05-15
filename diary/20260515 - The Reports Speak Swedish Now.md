# 20260515 — The Reports Speak Swedish Now

Today was the kind of session where you start with a review and end up rewriting half the engine.

## What happened

Before moving on to camper and house reports, I wanted a proper audit of everything in the financial advisor project and the financials folder. I ran three review agents in parallel — financial correctness, technical patterns, and readability — and they collectively surfaced a long list of real problems. Then I asked Claude to fix all of them, and to switch the report language to Swedish while doing it.

The Swedish translation layer went into `report.py` as three lookup dicts — `CATEGORY_SV`, `THEME_SV`, and `MONTH_SV` — with helper functions that fall back gracefully so nothing silently renders as English. Every section heading, column name, and month reference now comes out in Swedish. The data layer stays English internally; only the presentation flips.

Beyond the language switch: the income-zero fail-fast was added (so May 2026 surfaces immediately as "no salary imported" rather than reporting a -57k net), parking costs were folded into the monthly recurring TCO figures to close a ledger-vs-vehicle-report discrepancy, the SHA hash generation in the extractor was fixed so xlsx and pdf sources produce stable IDs, and the newest-file deduplication logic was corrected so the right export wins when two cover the same account.

The vehicle chart generator also got a fleet-level cost-per-10km chart and slices below 2% now group into "Övrigt" so the pie doesn't drown in noise. The vehicles report itself was rebuilt with all the corrected numbers and all three cars fully documented — no more "ej konfigurerad" placeholders.

## Interesting moments

The parking-in-TCO fix was the most satisfying puzzle. The ledger and the vehicle report had been disagreeing by a small but irritating amount — RKN218 by 8 kr/month, PTJ029 by 42, MSA52U by 42. The mismatch traced to parking costs being counted in the TCO summary but not in the monthly recurring total the ledger used. Adding parking to `MONTHLY_RECURRING` closed the gap exactly, and because the deposit increased by the same amount as the recurring expense, the running saldo numbers in the ledger tables didn't shift at all. A zero-sum fix that made everything line up.

## How it felt

[Not recorded]

## What's next

May 2026 reconciliation is waiting — it's the first month with the new MAT routing, and the salary import is missing. After that, camper and house reports.
