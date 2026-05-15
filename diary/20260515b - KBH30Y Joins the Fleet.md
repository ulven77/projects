# 20260515b — KBH30Y Joins the Fleet

A second session on the same day, this one narrower in scope but unexpectedly satisfying — the caravan finally gets a real entry in the model instead of being a vague line in the budget.

## What happened

The plan was to draft the camper report next from the existing fleet pattern. car.info knew it was an Adria Altea 502 UL (2020), bought 2022-03-03 from Haag & Carlsson Bil AB, but everything money-related had to be guessed: 195 000 kr purchase, 150 000 kr market, 2 400 kr/yr insurance, 400 kr/mo storage. The first cut was honest about being indikativ — every uncertain number marked `# TODO` in `vehicles.yaml`.

Then four screenshots showed up in `~/financials/data/kbh30y/`. The insurance was Folksam Husvagn med vagnskada at 631 kr/quarter (2 524 kr/yr). The loan was avtal 645300540675, ursprunglig skuld 211 200 kr at 4,7 % with 153 723 kr remaining over 130 months. The June 2026 invoice broke down as ränta 602 + amortering 1 173 + admin 45 = 1 820 kr scheduled, while the actual autogiro is 2 200 kr — so ~380 kr/mo extra principal is going in. Blocket comps for 2021 Adria Altea 502 UL were sitting at 219 900 / 249 000 / 249 000 kr, which after adjusting one year down for the 2020 model put real market value around 220 000 kr — far above the 150 000 kr estimate.

That rewrote the TCO. The replacement accrual dropped from 2 564 to 1 923 kr/mo because the caravan retains value much better than I'd modeled (residual revised to 150 000 kr at 2032, replacement to 300 000 kr in 2032 SEK). Loan interest + admin (647 kr/mo) moved into TCO as operating cost; amortization stayed out as balance-sheet. Then a one-line user message — "vagnen står på vår egen tomt" — wiped 4 800 kr/yr of storage, dropping the caravan's TCO to 36 864 kr/yr and the monthly set-aside to 3 072 kr.

To close out: the chart generator was extended to iterate `caravans:` alongside `vehicles:`, with caravan-aware burnup titles ("avsättning mot nästa husvagn") and the per-10km fleet chart explicitly cars-only. Three new PNGs — kbh30y_ledger, kbh30y_tco, kbh30y_burnup — landed in `~/financials/charts/` and got embedded in the report.

## Interesting moments

The most consequential moment was realizing the loan principal repayment doesn't belong in TCO. The earlier draft treated the full 2 200 kr/mo "Husvagnslån" as a financing line outside TCO entirely. But ränta + admin (647 kr/mo) is real operating cost — that's the price of using money this year. Only amortering is a balance-sheet movement (debt → asset). Splitting them gave a more honest fleet number: TCO captures consumption, the loan transaction in Gemensamt captures the cash. The 2032 handover math fell out for free — at byte time ~32 600 kr loan still outstanding vs ~150 000 kr residual = ~117 400 kr net down payment for the next caravan.

The other satisfying bit was the chart generator refactor. The old `main()` had `data['vehicles'].items()` hard-coded everywhere and per-reg dict lookups that would have KeyError'd on a caravan. Extracting `render_asset()` and pivoting to `{**cars, **caravans}` for combined loops took maybe ten minutes and meant the husvagn picked up ledger + TCO + burnup without any per-block special-casing.

## How it felt

[Not recorded]

## What's next

House report is the last asset in M2-Step1. After that, the May 2026 reconciliation — but the budget-net definition gap (April +27 181 in diary vs +9 181 in report.py) still needs to be tracked down first.
