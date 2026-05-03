## 20260503b — Commit skill: first real run, self-caught bug

**Type of work:** configuration, devops
**Repos touched:** aisafe/skills

**Session highlights:**
- Ran `/commit` skill for the first time in anger — it immediately surfaced a broken subagent reference
- `workspace-review` had been renamed to `arc42-review` but the pointer in `commit/SKILL.md` still used the old name
- Fixed reference, updated confirmation prompt to numbered list, committed as single refactor: "Fold workspace-review into commit as a subagent"

**Significant learnings:**
- A commit orchestrator that runs a workspace review will catch its own stale references — the skill validated itself on first use

**Pick up next time:** Push all unpushed commits (skills: 4 ahead, projects: 1 ahead), then start Hermes CSV loader

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
