# 20260510 — April Reconciliation Closes

Today the financial advisor stopped lying about April — every krona could be traced to where it actually went. Then the afternoon was spent turning that manual reconciliation process into a skill.

## What happened

The day began with restructuring how account metadata is stored. accounts.json got upgraded to accounts.yaml so descriptions, intended behaviours, and expected deviations could be written as proper multi-line prose instead of `\n`-littered JSON strings. PyYAML went into the Docker dependencies and the two pipeline scripts switched to `yaml.safe_load`. The format change was small in code but unlocked a much richer description of how each account behaves — what it should receive, what it should send, and what counts as a deviation.

From there the work was about getting the model right. Petra moved from household to external; tracking how she spends her allowance is not the household's job. The categorization rules were tightened to follow the new account model — date-bounded mortgage rules, a blanket pre-2024 "LÅN" rule for old freehand internal labels, specific family-transfer rules for known external account numbers, and the recognition that Swish is just a payment method, not a relationship signal.

Then came reconciliation. The first pass produced a difference of −1 416 kr. The second pass produced +5 318. Both were wrong because the opening balances were being read from the wrong end of the transaction list — the SEB export is reverse-chronological. Once the sort was fixed, the math identity held to the öre: tracked balance change +1 319 = budget net +27 181 minus 25 862 leakage to non-tracked counterparts.

In the afternoon the session pivoted to architecture. Rather than keep calling `make extract / categorize / report` by hand, the workflow got redesigned around a `/budget` skill with four phases: capture, categorize, reconcile, report. The old standalone `/reconcile` skill moved into the budget tree. The first phase built was reconcile — discrepancy walk, explicit categorize-rerun loop, then identity check. April was frozen as a facit and the new skill was dry-run against it. The discrepancy walk matched cleanly. The identity check revealed a gap: the skill's formula reproduces neither the diary's +27 181 budget net figure nor the +1 319 tracked balance change. Root cause partly traced (pairing is required for leakage classification; leg-by-leg classification mis-classifies every internal transfer) but the budget-net definition gap of 18 000 kr remains unresolved.

## Interesting moments

The MEDICINERCEL trace from the morning was satisfying — a single freehand Swedish word turned out to encode three separate legs of money flow across two days. The dry-run in the afternoon had the opposite satisfaction: it correctly refused to declare closure rather than silently report a false identity. The calibration step worked exactly as designed, catching the formula gap instead of hiding it.

## How it felt

[Not recorded]

## What's next

May 2026 is the first month with the new MAT routing (lön → Matvecka) — the annotation gets its real test. The improvements list still has eight open items (subscriptions to cancel, Apple charges to identify). The open thread going into tomorrow is the budget-net definition gap: the diary's +27 181 figure doesn't match report.py's +9 181 Overview Net and the formula that produced it hasn't been recovered yet. Until that's resolved, `/budget reconcile` runs in diagnostic mode.
