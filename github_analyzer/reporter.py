import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from github_analyzer.models import AnalysisResult


def render_terminal(result: AnalysisResult) -> str:
    console = Console(record=True, width=100)

    # Header
    console.print()
    console.print(
        Panel(
            f"[bold]GitHub Contributor Analysis: {result.repo}[/bold]\n"
            f"Period: last {result.period_days} days | {len(result.contributors)} contributors",
            style="bold cyan",
        )
    )

    # Table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="dim", width=4)
    table.add_column("Developer", width=16)
    table.add_column("Overall", justify="center", width=8)
    table.add_column("Commits", justify="center", width=8)
    table.add_column("Impact", justify="center", width=8)
    table.add_column("Collab", justify="center", width=8)
    table.add_column("Consistency", justify="center", width=11)

    ranked = result.ranked_contributors
    for i, contributor in enumerate(ranked, 1):
        grade_color = _grade_color(contributor.overall_grade)
        table.add_row(
            str(i),
            f"@{contributor.username}",
            f"[{grade_color}]{contributor.overall_grade}[/{grade_color}]",
            f"{contributor.commit_quality.clamped_value:.0f}",
            f"{contributor.code_impact.clamped_value:.0f}",
            f"{contributor.collaboration.clamped_value:.0f}",
            f"{contributor.consistency.clamped_value:.0f}",
        )
        if contributor.headline:
            table.add_row("", f'[dim]"{contributor.headline}"[/dim]', "", "", "", "", "")

    console.print(table)
    return console.export_text()


def render_json(result: AnalysisResult) -> str:
    ranked = result.ranked_contributors
    data = {
        "repo": result.repo,
        "period_days": result.period_days,
        "contributors": [
            {
                "username": c.username,
                "overall_grade": c.overall_grade,
                "overall_score": round(c.overall_score, 1),
                "scores": {
                    "commit_quality": c.commit_quality.clamped_value,
                    "code_impact": c.code_impact.clamped_value,
                    "collaboration": c.collaboration.clamped_value,
                    "consistency": c.consistency.clamped_value,
                },
                "headline": c.headline,
                "summary": c.summary,
            }
            for c in ranked
        ],
    }
    return json.dumps(data, indent=2)


def _grade_color(grade: str) -> str:
    if grade in ("A+", "A"):
        return "green"
    elif grade in ("B+", "B"):
        return "yellow"
    elif grade == "C":
        return "orange3"
    else:
        return "red"
