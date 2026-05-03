# 20260503 — Hermes Gets Its Blueprint

A day that started sleepy and ended with Hermes having a real architecture and a handful of new tools that haven't been tested yet.

## What happened

The morning opened badly — the CLAUDE.md on-load sequence hadn't fired at session start. No diary read, no symlink check. Caught it quickly, ran the sequence manually, confirmed the symlink was intact. A two-minute fix, but a reminder that being in context isn't the same as acting on it.

Then the real work began. Hermes got its architecture today. A 453-line arc42.md landed, documenting everything: the two-phase design where a Dockerized ingestion pipeline loads Swedish bank CSVs into a local DuckDB file, and a Marimo notebook handles interactive exploration and printable reports. ADRs cover the key decisions — Docker-only, BDD-first, DuckDB over SQLite, Marimo over Streamlit. The volume mount was wired up properly too: the container now reads from `shared/hellomessage.txt` instead of a hardcoded string, and the `.gitignore` was updated to make sure the DuckDB file with real bank data never gets committed.

In parallel, three skills were built from scratch: the arc42 skill (create and refresh), a workspace-review skill that became the commit subagent, and the commit orchestrator itself. By end of day the commit skill ran for the first time in anger — and immediately caught a broken reference in its own skill definition. Fixed it, added the numbered confirmation prompt, and committed clean.

## Interesting moments

One thing clicked today: Marimo over Streamlit. The choice makes sense because Marimo notebooks are reproducible and exportable, which matters when the output is a monthly cost report someone might actually print. The commit orchestrator ran for the first time too — it caught a broken filename in its own config, which is a good sign but not a real test. The tool is built and plausible. Whether it holds up on actual work is still an open question.

## How it felt

[Not recorded]

## What's next

Hermes has a blueprint. Now it needs data. The next step is the CSV loader — parse the three Swedish bank account files, map the columns (Bokföringsdatum, Text, Belopp, Saldo), and get a rolling two-month cost summary printing in the terminal. That's the first real milestone.
