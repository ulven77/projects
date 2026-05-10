# 20260510 — April Reconciliation Closes

Today the financial advisor stopped lying about April — every krona could be traced to where it actually went.

## What happened

The day began with restructuring how account metadata is stored. accounts.json got upgraded to accounts.yaml so descriptions, intended behaviours, and expected deviations could be written as proper multi-line prose instead of `\n`-littered JSON strings. PyYAML went into the Docker dependencies and the two pipeline scripts switched to `yaml.safe_load`. The format change was small in code but unlocked a much richer description of how each account behaves — what it should receive, what it should send, and what counts as a deviation.

From there the work was about getting the model right. Petra moved from household to external; tracking how she spends her allowance is not the household's job. Three of Petra's friends and family Swish numbers got proper external entries — Linnea, Ella, Johanna, Malin — with bank account numbers where known. The MEDICINERCEL transaction was traced from start to finish: a 2 500 kr refill from Hampus island into uffe hus, used to reimburse Ella for a medicine she had fronted. Internal transfer on its face, but worth recording as a deviation since uffe hus normally only reimburses Uffe's card spending. The categorization rules were tightened to follow the new account model — date-bounded mortgage rules, a blanket pre-2024 "LÅN" rule for old freehand internal labels, specific family-transfer rules for known external account numbers, and the recognition that Swish is just a payment method, not a relationship signal.

Then came reconciliation. The first pass produced a difference of −1 416 kr. The second pass produced +5 318. Both were wrong because the opening balances were being read from the wrong end of the transaction list — the SEB export is reverse-chronological. A screenshot from the SEB portal confirmed it: Gemensamt mat opened April with 7 243,65 kr and closed at 50,23 kr. Once the sort was fixed, the math identity held to the öre: tracked balance change +1 319 = budget net +27 181 minus 25 862 leakage to non-tracked counterparts.

## Interesting moments

The MEDICINERCEL trace was satisfying — a single freehand Swedish word turned out to encode three separate legs of money flow across two days. Find one, follow the chain, and the whole story falls out: Ella paid for medicine, Uffe didn't have enough in his house account, Hampus island refilled it, and the reimbursement landed back at Ella. Four transactions, one cohesive economic event.

The other moment that mattered was when the user pushed back on a rule change: "all swish transfers are not family transfers — Swish can come from any source and for any reason." That observation reshaped the rule design. Swish is the medium, not the meaning. A transfer's category should be about what it is, not how it got there. The fix was small but the principle is durable.

## How it felt

> _"good, reconsiliation was challenging."_
> ~ Ulf Rask

## What's next

May 2026 is the first month with the new MAT routing (lön → Matvecka), so that annotation gets its real test. The improvements list still has eight open items — subscriptions to cancel, Apple charges to identify, Klarna and Amazon Prime to move.
