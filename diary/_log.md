## 20260503c — Commit skill: first real run, self-caught bug

**Type of work:** configuration, devops
**Repos touched:** aisafe/skills

**Session highlights:**
- Ran `/commit` skill for the first time in anger — it immediately surfaced a broken subagent reference
- `workspace-review` had been renamed to `arc42-review` but the pointer in `commit/SKILL.md` still used the old name
- Fixed reference, updated confirmation prompt to numbered list, committed as single refactor

**Significant learnings:**
- A commit orchestrator that runs a workspace review will catch its own stale references — the skill validated itself on first use

**Pick up next time:** Start Hermes CSV loader — parse three Swedish bank account CSVs, map columns, print rolling 2-month cost summary

---

## 20260503b — Hermes architecture + three new skills

**Type of work:** coding, planning, configuration
**Repos touched:** aisafe/financial_project/hermes, aisafe/skills

**Session highlights:**
- Wrote 453-line `arc42.md` for Hermes: system context, container view, runtime scenarios, deployment view, and ADRs
- Key ADRs: Docker-only (network=none for ingestion), BDD-first, DuckDB over SQLite, Marimo over Streamlit
- Wired up volume mount: container now reads `shared/hellomessage.txt` instead of hardcoded string; BDD scenario updated
- Added `.gitignore` entries for DuckDB file (contains real bank data), SBOM, and generated artefacts
- Built arc42 skill (create + refresh subagents), workspace-review skill, and commit skill from scratch
- Updated `__todo.md`: goal reframed as "real data pipeline with DuckDB + Marimo" (no mock data needed)

**Significant learnings:**
- Marimo is preferred over Streamlit because notebooks are reproducible and exportable — matters when output is a printable monthly report
- DuckDB is the right fit here: embedded, zero-ops, fast on CSV, and safe to keep next to the code (just gitignore the file)
- arc42 ADRs are worth writing early — they make the "why" explicit before the code obscures it

**Pick up next time:** Hermes CSV loader — Step 1 of the real data pipeline

---

## 20260503 — CLAUDE.md on-load not firing

**Type of work:** debugging, configuration
**Repos touched:** aisafe/projects

**Session highlights:**
- Noticed CLAUDE.md on-load sequence (symlink check, diary read) didn't run at session start
- Ran the sequence manually; symlink was intact, no structural issue
- Root cause: behavioral — Claude must treat first message as a trigger to run on-load before responding

**Significant learnings:**
- On-load instructions in CLAUDE.md only fire if Claude actively reads and acts on them before the first response; being in context is not enough

**Pick up next time:** Start Hermes mock data — plan project structure and create two months of realistic financial data

---

## 20260502b — Planning + diary-on-load config

**Type of work:** planning, configuration
**Repos touched:** aisafe/projects, aisafe (USER_SCOPED_CLAUDE.md)

**Session highlights:**
- Added goals to `__todo.md`: GoPro Tandådalen (current), Hermes mock data (future), git commit skill with splitting (future)
- Updated `USER_SCOPED_CLAUDE.md`: Claude now reads diary/log on every session load for automatic context

**Significant learnings:**
- Having Claude read the diary on load removes the need to call `/session start` just to get oriented

**Pick up next time:** Edit GoPro Tandådalen footage in DaVinci Resolve; start with 2026-05-01 session

---

## 20260502 — Skills build: session + create-claude + create-skill improvements

**Type of work:** coding, configuration, devops
**Repos touched:** aisafe/skills, aisafe/projects

**Session highlights:**
- Built `session` skill from scratch: start/end router, diary-writer, session-logger, templates, full subagent structure
- Built `create-claude` skill: draft and review CLAUDE.md files at any scope (user, project, directory)
- Improved `create-skill` intent-clarification flow (committed: "Improve create-skill intent-clarification flow")
- System work: fixed apt mirror (se→main), installed DaVinci Resolve deps, fixed Ghostty xterm-ghostty terminfo, configured gdm3 display server

**Significant learnings:**
- Splitting diary-writing and session-logging into separate subagents (prose vs. structured data) keeps each focused and easier to tune
- Regional apt mirrors can silently serve stale package lists — switching to archive.ubuntu.com unblocked the system upgrade
- DaVinci Resolve on Linux requires libxcb-cursor0 and deliberate X11/Wayland configuration

**Pick up next time:** Commit and push pending skills changes (create-claude, session, deleted template/SKILL.md), then edit GoPro footage from 2026-05-01 in DaVinci Resolve

---
