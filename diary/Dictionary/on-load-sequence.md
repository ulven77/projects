# On-load sequence

**Instructions in CLAUDE.md that Claude should execute at the start of every session before responding to the first user message.**

A set of startup tasks — typically: check a symlink, read the diary/log for context, announce what was loaded. They live in CLAUDE.md so they apply across all sessions, but they only fire if Claude actively reads and acts on them when the session begins. Being present in context is not enough; Claude must treat the first message as a trigger. First surfaced clearly on 2026-05-03 when the sequence silently didn't run.

*First encountered: 2026-05-02 (built), 2026-05-03 (first failure noticed)*
