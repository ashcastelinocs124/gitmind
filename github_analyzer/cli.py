"""CLI entry point for AI GitHub Analyzer.

Provides the ``github-analyzer`` command with an ``analyze`` subcommand
that fetches contributor data, scores each contributor, optionally generates
AI summaries, and outputs results in terminal or JSON format.
"""

import os
import typer
from rich.console import Console
from github import GithubException
from github_analyzer.fetcher import GitHubFetcher
from github_analyzer.scorer import score_contributor
from github_analyzer.summarizer import generate_summaries
from github_analyzer.reporter import render_terminal, render_json
from github_analyzer.models import AnalysisResult

app = typer.Typer(help="AI GitHub Analyzer — grade developer effectiveness from repo contributions.")
console = Console()


@app.callback()
def main():
    """AI GitHub Analyzer — grade developer effectiveness from repo contributions."""


def _parse_repo(repo_url: str) -> str:
    """Extract 'owner/repo' from a URL or pass through if already in that format."""
    repo_url = repo_url.rstrip("/")
    if "github.com/" in repo_url:
        parts = repo_url.split("github.com/")[-1]
        return parts.split("/")[0] + "/" + parts.split("/")[1]
    return repo_url


@app.command()
def analyze(
    repo: str = typer.Argument(help="GitHub repo URL or 'owner/repo'"),
    token: str = typer.Option(None, "--token", "-t", envvar="GITHUB_TOKEN", help="GitHub personal access token"),
    days: int = typer.Option(90, "--days", "-d", help="Number of days to analyze"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Skip AI summary generation"),
):
    """Analyze all contributors in a GitHub repository."""
    if not token:
        console.print("[red]Error: GitHub token required. Use --token or set GITHUB_TOKEN env var.[/red]")
        raise typer.Exit(code=1)

    repo_name = _parse_repo(repo)

    try:
        with console.status("[bold green]Fetching data from GitHub..."):
            fetcher = GitHubFetcher(token=token)
            contributor_stats = fetcher.fetch(repo_name, days=days)
    except GithubException as e:
        console.print(f"[red]GitHub API error: {e.data.get('message', 'Unknown error') if hasattr(e, 'data') and e.data else e}[/red]")
        raise typer.Exit(code=1)
    except Exception:
        console.print("[red]Failed to fetch data from GitHub. Check your token and repo URL.[/red]")
        raise typer.Exit(code=1)

    if not contributor_stats:
        console.print("[yellow]No contributors found in the specified period.[/yellow]")
        raise typer.Exit(code=0)

    total_commits = sum(s.total_commits for s in contributor_stats.values())

    with console.status("[bold green]Scoring contributors..."):
        reports = []
        for stats in contributor_stats.values():
            report = score_contributor(stats, total_repo_commits=total_commits, period_days=days)
            reports.append(report)

    if not no_ai:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            try:
                with console.status("[bold green]Generating AI summaries..."):
                    generate_summaries(reports, api_key=api_key)
            except Exception:
                console.print("[yellow]Warning: AI summary generation failed. Showing scores only.[/yellow]")
        else:
            console.print("[dim]Skipping AI summaries (OPENAI_API_KEY not set)[/dim]")

    result = AnalysisResult(repo=repo_name, period_days=days, contributors=reports)

    if json_output:
        print(render_json(result))
    else:
        print(render_terminal(result))


if __name__ == "__main__":
    app()
