# commit-orchestrator

**A skill pattern that wraps the full commit workflow: workspace review → split analysis → staged diff → message draft → markdown review → confirmed execution.**

Rather than running git commands directly, a commit orchestrator runs a structured pre-flight before any code lands: it discovers all repos, surfaces pending changes, checks for diagram drift, analyses whether changes should be split into multiple commits, and presents a formatted review block for confirmation. Nothing is staged or committed until the human explicitly approves. First used in the `/commit` skill (2026-05-03), where the pattern immediately caught a stale subagent reference in its own skill definition.

*First encountered: 2026-05-03*
