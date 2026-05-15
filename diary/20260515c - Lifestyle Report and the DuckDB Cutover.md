# 20260515c — Lifestyle Report and the DuckDB Cutover

Third session of the day, and the one that turned a "let's draft the rest of the consumption reports" into a structural change for how transaction data is going to be worked with from now on.

## What happened

After the caravan landed in the morning's b session, the natural next step was the consumption side — recurring services, food, allowances, one-offs, unsecured loans. The framing was easy: "all of them at once, they should be straightforward." The data wasn't. A first pass through `categorized_transactions.json` surfaced 484 278 kr in Uncategorized over 12 months, a `RKN218` category that was a routing bug, Klarna and Ecster amortizations sitting in Online shopping, and an Insurance bucket that the asset reports were only half-accounting for. The "straightforward" report still got written — `lifestyle-financial-reality-report-2026.sv.md`, ten sections, three new charts, honest about every gap and with an ordered åtgärdslista at the end — but the data quality problem was now too prominent to ignore.

So the second half of the session was the structural change: move transaction data into a real database. DuckDB won the comparison against SQLite, TinyDB, and the document-DB framing on the grounds that the workload is analytical first, document-shaped second. The migration script reads the JSON, the new schema preserves the 8-char SHA as a non-unique reference column (because SEB exports contain ~2.5 % true duplicates — same date, account, description, amount, all four matching), and an auto-increment `pk` becomes the real primary key. Auxiliary tables for `category_rules`, `categorization_history`, and `improvements` round out the model, and three views (`v_monthly_category`, `v_uncategorized_top`, `v_recurring_merchants`) cover the most common ad-hoc questions.

Then the workbench: a `TransactionDB` Python helper, a `workbench.py` CLI with subcommands (`uncategorized`, `find`, `reclassify`, `history`, `sql`, `summary`), and a `wb` bash wrapper that runs it in Docker matched to the host user. The whole thing got exercised end-to-end by applying the two cleanups identified in the lifestyle report: ECSTER + K* KLARNA (64 txs, ~37 900 kr) moved to a new `Klarna repayment` category, and BENSIN/AVGIFT RÄKAN (20 txs, 15 500 kr) moved out of the bogus `RKN218` category into Internal transfers. Both ran with `--dry-run` first, then for real, leaving 84 audit rows in `categorization_history` tagged with rules `klarna-2026-05-15` and `rkn218-route-2026-05-15`.

## Interesting moments

The SHA-collision discovery was the moment the schema design earned its keep. The first migration attempt blew up with a primary-key violation on `001190ca`. Two transactions on the same day, same account, same amount, same description — legitimately distinct (back-to-back transfers happen), but the hash function couldn't tell them apart. 259 collisions in total. The reflexive fix was "make SHA truly unique by adding source_file to the hash input" — but that would break the existing convention that every transaction row in every report carries the same stable 8-char identifier. So instead: keep SHA as the human-friendly reference (still 8 chars, still in every table), drop the uniqueness constraint, and introduce `pk` as the real primary key. 97.5 % of references stay unambiguous; the 2.5 % that collide need a date/amount qualifier when cited. That trade-off feels right — the user-facing convention survives, the database stays sound.

The Docker permission dance was a smaller but worth-noting moment. The first migration created the .duckdb file as root, which made the local DuckDB CLI fail with EACCES. The fix — `docker run -u $(id -u):$(id -g) ... -e HOME=/tmp` — also became the template for the `wb` wrapper, so every workbench invocation now writes files owned by `uven`. Friction once, smooth forever.

## How it felt

[Not recorded]

## What's next

Agentic categorization is now the natural Shortterm goal sitting on top of the DuckDB foundation — work through the Uncategorized backlog in batches, each ending with a rule row so the same cleanup happens automatically on the next SEB import. After that, the `categorize.py` and `report.py` cutover to use DuckDB instead of JSON.
