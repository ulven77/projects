# 20260521 — What The Accounts Are Actually Doing

A session that started as "make a pedagogical flowchart" and turned into a mirror held up to the household's account model. The map got drawn cleanly enough. What it reflected was that the mental model and the actual money movement have been drifting apart for a long time.

## What happened

The first ask was simple: a `account-flow.md` report — Mermaid flowchart with the accounts as boxes and `account_flows.yaml`'s 18 edges as arrows, plus tables and a legend. A 285-line generator script `generate_account_flow_report.py` was written to render it deterministically from YAML, in the same spirit as the existing vehicle and lifestyle generators. First version with `flowchart TD` (top-down); the user asked for left-to-right; one-line change to `flowchart LR`. Then "put personal accounts at the bottom" — required pulling Uffe betalkonto and Petra personal into their own subgraph declared last (Mermaid stacks subgraphs vertically in declaration order). Gold palette to distinguish them from the SEB/Lysa/external groupings.

Then the user looked at the rendered chart against their mental model — they'd sketched a tidy hub-and-spoke with Gemensamt lön at the center and everything (including ISK, Lysa, Ella försäkringspengar) flowing out from there. The data shows nothing of the sort. Sparflöden go via räkningar: räkningar → ISK Månadssparande, räkningar → Lysakonto autogiro, ISK → Länsförsäkringar fund. Five years of data, zero direct lön → ISK or lön → Lysa flows.

That observation got documented as Deviation #1 (severity 🟡) in a new `deviations:` block at the bottom of `account_flows.yaml`. The generator grew a `render_deviations()` function that emits an "Observerade avvikelser" section with severity badges, structured intent-vs-observed-vs-evidence-vs-actions per entry.

Then Deviation #2 went in (severity 🔴). A SQL drill into lön's actual outgoing patterns surfaced 185 distinct descriptions over the last 12 months. Beyond the documented internal pipeline, lön has been used as a direct expense account: 116 kkr direct to mat (kringgår the Matvecka pipeline), 19 kkr försäkringspremier, 18 kkr Linneas månadspeng, 15,5 kkr to RKN218's bensinkonto-fund (BENSIN RÄKAN + AVGIFT RÄKAN — but those should be Internal Transfers anyway since they go to a tracked account), 13 kkr to gemensamt kök (which accounts.yaml says is dormant), plus a stream of direct ICA/HEMKOP/GRANNGÅRDEN groceries on what's supposed to be the income hub's card. And — the one that the user genuinely doesn't recognize — 31 kkr/year going to account `56900725627` across 20 transactions. Account number not in accounts.yaml. Same account also shows up as Batch 2 in the agentic-categorization shortterm goal.

Deviation #3 was Petras allowance. accounts.yaml says ~3 000 kr/mo, data shows 3 transactions over 12 months in unpredictable amounts (3 000, 9 000, and 500 kr).

The user paused at this point and parked the work as a new shortterm goal: "Konto-modellöversyn — fundera på hur kontona faktiskt används." Three open questions noted for the future-self: what is 56900725627; should lön be renoda-d back to a pure distribution nav; or should the model be updated to acknowledge lön as "income + ad-hoc spend"?

## Interesting moments

The drift between the sketched mental model and the data is the kind of finding that makes account-modeling worth doing in the first place. The user expected to see a flat hub-and-spoke from lön. The reality is a two-level pyramid (lön → räkningar → savings) with significant lateral leakage (lön → mat directly, lön → 56900725627). Neither is wrong per se — the question is whether the structural choice was deliberate or accidental. Looking at the smaller transactions (ICA on lön's card, kök-account top-ups for a "dormant" account, the unknown 56900725627), it reads more accidental than designed.

The other small but lovely moment was Mermaid's subgraph-ordering quirk paying off cleanly. In `flowchart LR`, subgraphs stack vertically in declaration order. By moving the personal-accounts subgraph to last in the generator, they slide to the bottom of the diagram with zero positioning hacks. Sometimes the platform just behaves the way you'd expect.

## How it felt

[Not recorded]

## What's next

The Konto-modellöversyn is parked until you've had time to think. When you come back: pick a direction (renoda lön vs accept-and-document) and chase down 56900725627. Until then, P6 reports (Reserve Funding Ratio, Function/Object Life-Allocation pies) and the budget-net definition gap from May reconciliation are the next available work.
