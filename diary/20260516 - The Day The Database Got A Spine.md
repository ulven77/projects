# 20260516 — The Day The Database Got A Spine

A foundation day. By the end of it, every transaction in the household's six-year financial history sat in a properly-shaped relational store with a double-entry invariant — and there were finally tables in place for things the JSON pipeline could never represent.

## What happened

The session started by adding Lysa as a first-class account namespace in `accounts.yaml`. A new top-level `lysa:` block sits alongside `household:` and `external:`, keyed by Lysa's UUIDs (because Lysa doesn't use SEB-style 11-digit account numbers). Four accounts went in: Lysakonto, Sparkonto, Bred (closed), Ella Försäkringspengar. Two iterations on the file as the Lysa export got refined: first the old export, then a renamed-and-cleaned version where Lysakonto 2 got consolidated into Lysakonto, Bred disappeared, and a new "Renoveringsfond Frönäs 5:9" (1 kr seed) appeared — matching the housing report's previously-mysterious "Lysakonto 3" reference. Mystery resolved.

Then a deeper conversation about the accounts.yaml schema itself. SEB won't let the household open or close accounts freely, so the same account number gets repurposed over the years. The same key (`56990319038`) might have been a boat-purchase fund yesterday and Ella's mobile-phone account today. The flat `name:` field couldn't capture that history. We agreed on a `roles[]`-list schema: each account becomes a list of date-bounded role entries with `name`/`from`/`to`/`description`/`intended_behaviours`/`expected_deviations`. Newest role first; transition day belongs to the new role; `null` means open-ended. All 17 household accounts migrated to single-element role lists. Categorizer code gets a `role_at(account, tx_date)` helper for free.

Then the big work: P1 of the categorization rework. The DuckDB schema was rewritten with proper separation between observation and interpretation. `tx` became immutable bank rows with a unique SHA primary key — but the existing SHA scheme had 259 collisions across 10 678 rows because two same-day same-amount same-description back-to-back transfers hash identically. The fix: include `occurrence_within_group` in the hash input. Now every SHA is unique and re-importing the same export is an idempotent no-op (the PK enforces it). The 259 "true duplicates" got distinct hashes that stay stable across re-imports because SEB's export ordering is stable.

`sub_tx` is the new classification carrier. Every tx has ≥ 1 sub_tx; bundled payments (loan = interest + amortization + admin; bundled insurance covering multiple assets) split into N sub_tx with separate `category`/`economic_function`/`object` tags. The invariant: `SUM(sub_tx.amount WHERE tx_sha = X) = tx.amount`. A new view `v_split_integrity` returns violators (must be empty). Two more tables: `recurring` for expected cashflow contracts (vendor pattern, expected amount, expected_months, splits), and `account_flow` for the household money pipeline graph.

The migration ran clean: 10 678 tx → 10 678 sub_tx (1:1 baseline), zero integrity violations. The two known cleanups (ECSTER + K\* KLARNA → Klarna repayment, BENSIN/AVGIFT RÄKAN → Internal transfers) were re-applied at sub_tx level with audit history. `transaction_db.py` and `workbench.py` got rewritten to operate on sub_tx with the joined `v_tx_sub` view as the primary query surface.

## Interesting moments

The SHA-collision discovery was the moment the schema design earned its keep. The first migration attempt blew up with a PRIMARY KEY violation on `001190ca`. Two transactions on the same day, same account, same amount, same description — legitimately distinct events that the content hash couldn't tell apart. The reflexive fix was "make SHA truly unique by adding source_file to the hash input" — but that would break the existing convention that every transaction row in every report carries the same stable 8-char identifier. The cleaner fix: occurrence-within-group as part of the hash input. 97.5 % of references stay unambiguous; the 2.5 % that collided now resolve cleanly, and the PRIMARY KEY constraint becomes real.

The `roles[]` schema decision was the other moment. The user explained that SEB caps account count, so accounts get repurposed. They sketched the schema: each entry becomes a list of time-bounded roles. The "boat purchase" example they used to illustrate it turned out to be illustrative, not real — but the example became prophetic by end of day, because the orphan-flow analysis (next day's session) surfaced a 253 900 kr "Ella mobil → Lön" pattern that strongly suggests account 56990319038 actually was a project earmark before its current dormant role.

## How it felt

[Not recorded]

## What's next

P2 — populate `account_flow` from accounts.yaml prose so internal-transfer auto-classification has structure to lean on.
