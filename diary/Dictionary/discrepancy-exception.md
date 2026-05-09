# Discrepancy Exception

**A named carve-out that excludes a specific transaction from both flow rule checks and monthly limit calculations.**

In the financial advisor pipeline, discrepancy exceptions are stored in `categories.json` keyed by 8-char SHA ID. When a transaction ID appears in the exceptions list, it is skipped during flow rule violation detection and removed from per-category spend totals before limit thresholds are evaluated. Each exception carries a human-readable label that appears as a Documentation link in the Transfers section of the report, with the full explanation living in `discrepancy_log.md` at a matching HTML anchor. This pattern emerged on 2026-05-09 to handle one-off events — a March allowance paid April 1st, a birthday gift forwarded to a partner — without triggering false alarms every month.

*First encountered: 2026-05-09*
