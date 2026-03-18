import json
from github_analyzer.reporter import render_terminal, render_json
from github_analyzer.models import AnalysisResult, ContributorReport, DimensionScore


def _make_result():
    r1 = ContributorReport(
        username="alice",
        commit_quality=DimensionScore(name="Commit Quality", value=90),
        code_impact=DimensionScore(name="Code Impact", value=85),
        collaboration=DimensionScore(name="Collaboration", value=80),
        consistency=DimensionScore(name="Consistency", value=75),
        headline="Strong all-around contributor",
        summary="Alice is a consistent, high-impact developer.",
    )
    r2 = ContributorReport(
        username="bob",
        commit_quality=DimensionScore(name="Commit Quality", value=60),
        code_impact=DimensionScore(name="Code Impact", value=55),
        collaboration=DimensionScore(name="Collaboration", value=50),
        consistency=DimensionScore(name="Consistency", value=45),
    )
    return AnalysisResult(repo="owner/repo", period_days=90, contributors=[r1, r2])


def test_render_terminal_returns_string():
    result = _make_result()
    output = render_terminal(result)
    assert isinstance(output, str)
    assert "alice" in output
    assert "bob" in output
    assert "owner/repo" in output


def test_render_terminal_shows_grades():
    result = _make_result()
    output = render_terminal(result)
    assert "A" in output


def test_render_json_returns_valid_json():
    result = _make_result()
    output = render_json(result)
    parsed = json.loads(output)
    assert parsed["repo"] == "owner/repo"
    assert parsed["period_days"] == 90
    assert len(parsed["contributors"]) == 2
    assert parsed["contributors"][0]["username"] == "alice"
    assert "overall_grade" in parsed["contributors"][0]
    assert "overall_score" in parsed["contributors"][0]
    assert "scores" in parsed["contributors"][0]
