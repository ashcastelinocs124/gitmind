# Memory

## Current State
- Project: AI GitHub Analyzer — brainstorming complete, design approved
- Design doc: `docs/plans/2026-03-17-github-analyzer-design.md`
- Next step: implementation planning

## Key Decisions
- **Form factor:** Python CLI tool (typer)
- **Scoring:** 4 heuristic dimensions — Commit Quality (25%), Code Impact (30%), Collaboration (25%), Consistency (20%)
- **AI:** OpenAI GPT-4o for natural language summaries only; scoring is purely heuristic
- **Output:** Rich terminal by default, `--json` flag for machine consumption
- **Auth:** User-provided GitHub token (env var or CLI flag)
- **Scope:** Analyze all contributors, default 90-day window
- **Integration:** ClubClaw autonomous agent platform calls via subprocess once/week
- **Dependencies:** typer, pygithub, rich, openai
