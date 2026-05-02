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
