# AI GitHub Analyzer — Design Document

**Date:** 2026-03-17
**Status:** Approved

## Summary

A Python CLI tool that analyzes all contributors in a GitHub repo, scores them on four dimensions using heuristics, and generates AI summaries via OpenAI. Designed for human use (rich terminal output) and integration with ClubClaw autonomous agent platform (JSON output via `--json` flag). ClubClaw calls it as a subprocess once per week.

## Architecture

Monolithic Python CLI with clean internal modules:

```
github-analyzer/
├── cli.py              # Typer CLI entry point
├── fetcher.py          # GitHub API data collection (PyGithub)
├── scorer.py           # Heuristic scoring engine
├── summarizer.py       # OpenAI summary generation
├── reporter.py         # Terminal (rich) + JSON output
└── models.py           # Data classes for contributors, scores, metrics
```

Single command: `github-analyzer analyze <repo-url> [--json] [--token TOKEN] [--days N] [--no-ai]`

Flow: Fetch all contributor data → Score each contributor across 4 dimensions → Call OpenAI to generate summaries → Output report.

## Scoring Dimensions

Four heuristic-based scores, each 0–100, combined into a weighted overall grade.

### Commit Quality (25%)
- Commit message length and descriptiveness
- Commit size — penalize massive dumps, reward atomic commits
- Code churn ratio — how often they rewrite their own recent code
- Lines added vs deleted balance (pure additions vs thoughtful refactoring)

### Code Impact (30%)
- Code survivability — % of their code still in the repo (not reverted/overwritten)
- Touches to critical files (core modules vs docs/config)
- Complexity of files they modify (proxy via file size, number of functions)
- Net contribution — total lines surviving in current codebase

### Collaboration (25%)
- PR review comments given to others
- Issue participation (opening, commenting, closing)
- PR approval/rejection ratio on their own PRs
- Review turnaround time

### Consistency & Patterns (20%)
- Commit regularity (steady cadence vs sporadic bursts)
- Breadth of codebase touched (bus factor contribution)
- Streak length and active weeks ratio
- Time-of-day/day-of-week patterns (informational only)

### Overall Grade
Weighted average mapped to letter grades: A+, A, B+, B, C, D, F.

## Data Fetching

Using PyGithub to collect from the GitHub REST API:

- **Commits:** All commits with author, message, date, stats (additions/deletions/files changed)
- **Pull Requests:** All PRs with author, reviewers, comments, approval status, merge status
- **Issues:** All issues with participants, comments, labels
- **Reviews:** PR review comments and review decisions

### Scope
- Default: last 90 days of activity
- `--days N` flag to customize
- GitHub token via `--token` flag or `GITHUB_TOKEN` env var
- PyGithub handles rate limit awareness automatically

## AI Summaries

After scoring, each contributor's metrics are sent to OpenAI GPT-4o:

**Input:** Scores across 4 dimensions, key stats, rank relative to others.

**Output:**
- 2-3 sentence summary of strengths and weaknesses
- One-line headline characterization

**Config:**
- `OPENAI_API_KEY` env var
- `--no-ai` flag to skip summaries (raw scores only)
- Model: `gpt-4o`

## CLI Interface

```bash
# Basic usage
github-analyzer analyze https://github.com/owner/repo

# With options
github-analyzer analyze https://github.com/owner/repo --days 180 --json --no-ai
```

### Terminal Output (default)
Rich formatted table with rank, developer, per-dimension scores, overall grade, and AI summary.

### JSON Output (--json)
Structured JSON with repo info, period, and array of contributors with scores and summaries. Designed for ClubClaw consumption.

## Dependencies

- `typer` — CLI framework
- `pygithub` — GitHub API client
- `rich` — Terminal formatting
- `openai` — AI summary generation

## Integration

ClubClaw autonomous agent platform calls this tool as a subprocess once per week:
```bash
github-analyzer analyze <repo-url> --json
```
Parses JSON output for its reporting pipeline.
