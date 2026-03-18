# Memory

## Current State
- Project: AI GitHub Analyzer -- Tasks 1-9 complete (Scaffolding, Models, Fetcher, Scoring Engine, Summarizer)
- Design doc: `docs/plans/2026-03-17-github-analyzer-design.md`
- Implementation plan: `docs/plans/2026-03-17-github-analyzer-implementation.md`
- Git repo initialized, 5 commits made
- Package installed in editable dev mode (`pip install -e ".[dev]"`)
- Models defined in `github_analyzer/models.py` with 6 passing tests in `tests/test_models.py`
- Fetcher in `github_analyzer/fetcher.py` with 4 passing tests in `tests/test_fetcher.py`
- Scoring engine in `github_analyzer/scorer.py` with 12 passing tests in `tests/test_scorer.py`
- Summarizer in `github_analyzer/summarizer.py` with 3 passing tests in `tests/test_summarizer.py`
- Total: 25 passing tests
- Next step: Task 10 -- Reporter (Terminal + JSON)

## Key Decisions
- **Form factor:** Python CLI tool (typer)
- **Scoring:** 4 heuristic dimensions — Commit Quality (25%), Code Impact (30%), Collaboration (25%), Consistency (20%)
- **AI:** OpenAI GPT-4o for natural language summaries only; scoring is purely heuristic
- **Output:** Rich terminal by default, `--json` flag for machine consumption
- **Auth:** User-provided GitHub token (env var or CLI flag)
- **Scope:** Analyze all contributors, default 90-day window
- **Integration:** ClubClaw autonomous agent platform calls via subprocess once/week
- **Dependencies:** typer, pygithub, rich, openai
