# Calibration step

**A built-in sanity check that verifies a formula reproduces known-good historical numbers before trusting it on new data.**

In the /budget reconcile skill, the calibration step re-runs the three-term reconciliation identity against April 2026's verified close (+1 319 = +27 181 − 25 862) every time the skill runs. If the formula doesn't reproduce those numbers, it surfaces the mismatch loudly instead of silently proceeding. The value is asymmetric: a false ✓ hides a wrong formula; a false ✗ just means more investigation. Better to surface uncertainty than to declare a closure that isn't real.

*First encountered: 2026-05-10*
