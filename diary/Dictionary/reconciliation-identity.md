# Reconciliation identity

**Tracked balance change = Budget net − Leakage to non-tracked counterparts.**

The accounting fact that makes household reconciliation possible. Money flowing out of tracked accounts (household section of accounts.yaml) to non-tracked counterparts (Petra's personal account, friends' Swish numbers, external loans) doesn't land in the budget — it leaks. The three-term identity accounts for this: tracked balance change = budget net − net leakage. When the identity holds, every krona is explained; when it doesn't, either categorisation is wrong, balance data is misread, or leakage classification missed a counterpart.

Pairing via `report.py:build_transfer_pairs` is mandatory for leakage calculation — SEB shows only the sender's personal name on incoming legs, so leg-by-leg classification mis-classifies every internal pair as "unknown counterpart".

First closed for April 2026: +1 319 = +27 181 − 25 862 (per the 2026-05-10 diary). The budget-net figure of +27 181 is +18 000 kr larger than report.py's Overview Net for April — the definition gap is an open issue as of 2026-05-10 and has not yet been recovered in code.

*First encountered: 2026-05-10*
