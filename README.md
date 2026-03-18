# AI GitHub Analyzer

A Python CLI tool that analyzes all contributors in a GitHub repository, scores them across four dimensions using heuristics, and generates AI-powered natural language summaries via OpenAI. Built for both human use (rich terminal output) and programmatic integration (JSON output).

## Features

- **Four-Dimension Scoring** — Grades developers on Commit Quality (25%), Code Impact (30%), Collaboration (25%), and Consistency (20%)
- **AI-Powered Summaries** — Uses OpenAI GPT-4o to generate natural language assessments of each contributor's strengths and areas for improvement
- **Rich Terminal Output** — Color-coded leaderboard with grades, per-dimension scores, and AI headlines
- **JSON Output** — Machine-readable output for integration with other tools and automation pipelines
- **Flexible Time Windows** — Analyze any time period (default: last 90 days)

## Scoring Dimensions

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| **Commit Quality** | 25% | Message descriptiveness, commit size discipline, code churn balance |
| **Code Impact** | 30% | Net lines contributed, commit share, file breadth, merged PRs |
| **Collaboration** | 25% | PR reviews given, issue participation, PR merge rate |
| **Consistency** | 20% | Week-over-week regularity, commit spread evenness |

Scores are combined into an overall grade: A+, A, B+, B, C, D, or F.

## Requirements

- Python 3.11+
- A [GitHub Personal Access Token](https://github.com/settings/tokens) with `repo` scope
- (Optional) An [OpenAI API key](https://platform.openai.com/api-keys) for AI-generated summaries

## Installation

```bash
git clone https://github.com/ashcastelinocs124/ai-github-analyst.git
cd ai-github-analyst
pip install -e ".[dev]"
```

## Usage

### Basic Analysis

```bash
# Recommended: set the token as an environment variable
export GITHUB_TOKEN=your_token_here
github-analyzer analyze owner/repo

# Or pass it directly (note: this will appear in shell history)
github-analyzer analyze https://github.com/owner/repo --token YOUR_GITHUB_TOKEN
```

> **Security note:** Prefer using the `GITHUB_TOKEN` environment variable over the `--token` flag. CLI arguments are visible in shell history and process listings.

### Options

```bash
# Analyze last 180 days instead of default 90
github-analyzer analyze owner/repo --days 180

# Output as JSON (for programmatic use)
github-analyzer analyze owner/repo --json

# Skip AI summaries (faster, no OpenAI key needed)
github-analyzer analyze owner/repo --no-ai

# Combine options
github-analyzer analyze owner/repo --days 60 --json --no-ai
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub Personal Access Token (alternative to `--token` flag) |
| `OPENAI_API_KEY` | No | OpenAI API key for AI-generated summaries |

### Example Output

```
╔══════════════════════════════════════════════════════════╗
║          GitHub Contributor Analysis: owner/repo         ║
║          Period: last 90 days | 5 contributors           ║
╚══════════════════════════════════════════════════════════╝

 Rank  Developer       Overall  Commits  Impact  Collab  Consistency
 ──────────────────────────────────────────────────────────────────────
  1.   @alice            A+       92       88      95       90
       "Reliable core contributor with strong review habits"
  2.   @bob              B+       78       82      70       75
       "High-impact coder, could engage more in reviews"
```

## Architecture

```
github_analyzer/
├── cli.py              # Typer CLI entry point
├── fetcher.py          # GitHub API data collection (PyGithub)
├── scorer.py           # Heuristic scoring engine (4 dimensions)
├── summarizer.py       # OpenAI GPT-4o summary generation
├── reporter.py         # Terminal (Rich) + JSON output rendering
└── models.py           # Dataclasses for contributors, scores, results
```

**Data flow:** CLI → Fetcher (GitHub API) → Scorer (heuristics) → Summarizer (OpenAI) → Reporter (output)

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Run a specific test file
pytest tests/test_scorer.py -v
```

## Dependencies

| Package | Purpose |
|---------|---------|
| [typer](https://typer.tiangolo.com/) | CLI framework |
| [PyGithub](https://pygithub.readthedocs.io/) | GitHub REST API client |
| [Rich](https://rich.readthedocs.io/) | Terminal formatting and tables |
| [openai](https://platform.openai.com/docs/) | AI summary generation |

## License

MIT
