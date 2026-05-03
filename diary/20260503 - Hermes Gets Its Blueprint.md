# 20260503 — Hermes Gets Its Blueprint

A day that started sleepy and ended with real numbers visible in a notebook.

## What happened

The morning opened badly — the CLAUDE.md on-load sequence hadn't fired at session start. No diary read, no symlink check. Caught it quickly, ran the sequence manually, confirmed the symlink was intact. A two-minute fix, but a reminder that being in context isn't the same as acting on it.

Then the real work began. Hermes got its architecture — a 453-line arc42.md documenting the two-phase design: a Dockerized ingestion pipeline loading Swedish bank CSVs into DuckDB, and a Marimo notebook for interactive exploration. ADRs cover the key decisions: Docker-only, BDD-first, DuckDB, Marimo over Streamlit. Three skills were also built from scratch: arc42, workspace-review (later folded into the commit subagent), and the commit orchestrator.

In the afternoon the pipeline became real. The Makefile was fixed to mount the actual data directory, then the full implementation landed: a CSV loader that strips account numbers at the ingestion boundary (only friendly names reach the database), a DuckDB writer, a Marimo notebook served inside Docker on port 2718, and Behave tests validating the whole pipeline using in-memory DuckDB. `make ingest` loaded 8115 transactions from three accounts. `make test` passed all 14 steps. `make notebook` opened the browser and real numbers appeared.

## Interesting moments

The account number decision was the right call: the ingestion container has no network access and strips all account numbers before writing to DuckDB, so the notebook — which does need network to serve its UI — never sees anything sensitive. Privacy by architecture, not by policy.

## How it felt

_"Good, I see numbers in a notebook. So now we just need to find a way to categorize expenses and start making reports."_
~ Ulf Rask

## What's next

Categorize transactions — define keyword rules (HEMKOP → Groceries, TELIA → Telecom) and apply them during ingestion or as a query layer. Then build the report view in the notebook: costs by category, per account, rolling two months.
