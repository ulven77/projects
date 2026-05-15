# Fail-fast discrepancy

**A guard that fires before the main report logic and surfaces a blocking data problem immediately, rather than letting the report silently produce wrong numbers.**

In `report.py`, the income-zero check is the canonical example: if `total_income == 0` after categorization, a `"zero_income"` discrepancy is appended and the Förbättringar section makes it visible. Without this, a month with a missing salary import would render as a valid −57 000 kr net rather than flagging the missing data. The pattern generalises: any precondition that, if violated, makes downstream calculations meaningless is a candidate for a fail-fast discrepancy.

*First encountered: 2026-05-15*
