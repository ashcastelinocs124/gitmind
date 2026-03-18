from github_analyzer.models import (
    ContributorStats,
    DimensionScore,
    ContributorReport,
    AnalysisResult,
    score_to_grade,
)


def test_dimension_score_clamps_to_0_100():
    score = DimensionScore(name="test", value=150)
    assert score.clamped_value == 100

    score2 = DimensionScore(name="test", value=-10)
    assert score2.clamped_value == 0


def test_contributor_stats_defaults():
    stats = ContributorStats(username="alice")
    assert stats.username == "alice"
    assert stats.total_commits == 0
    assert stats.total_prs == 0
    assert stats.total_reviews == 0
    assert stats.total_issues == 0
    assert stats.commits == []
    assert stats.pull_requests == []
    assert stats.reviews == []
    assert stats.issues == []


def test_contributor_report_overall_score():
    report = ContributorReport(
        username="alice",
        commit_quality=DimensionScore(name="Commit Quality", value=80),
        code_impact=DimensionScore(name="Code Impact", value=90),
        collaboration=DimensionScore(name="Collaboration", value=70),
        consistency=DimensionScore(name="Consistency", value=60),
    )
    # Weighted: 80*0.25 + 90*0.30 + 70*0.25 + 60*0.20 = 20+27+17.5+12 = 76.5
    assert report.overall_score == 76.5


def test_score_to_grade():
    assert score_to_grade(95) == "A+"
    assert score_to_grade(90) == "A+"
    assert score_to_grade(85) == "A"
    assert score_to_grade(80) == "A"
    assert score_to_grade(75) == "B+"
    assert score_to_grade(70) == "B+"
    assert score_to_grade(65) == "B"
    assert score_to_grade(60) == "B"
    assert score_to_grade(55) == "C"
    assert score_to_grade(50) == "C"
    assert score_to_grade(45) == "D"
    assert score_to_grade(40) == "D"
    assert score_to_grade(30) == "F"


def test_contributor_report_grade():
    report = ContributorReport(
        username="alice",
        commit_quality=DimensionScore(name="Commit Quality", value=90),
        code_impact=DimensionScore(name="Code Impact", value=90),
        collaboration=DimensionScore(name="Collaboration", value=90),
        consistency=DimensionScore(name="Consistency", value=90),
    )
    assert report.overall_grade == "A+"


def test_analysis_result_sorted_by_score():
    r1 = ContributorReport(
        username="low",
        commit_quality=DimensionScore(name="Commit Quality", value=30),
        code_impact=DimensionScore(name="Code Impact", value=30),
        collaboration=DimensionScore(name="Collaboration", value=30),
        consistency=DimensionScore(name="Consistency", value=30),
    )
    r2 = ContributorReport(
        username="high",
        commit_quality=DimensionScore(name="Commit Quality", value=90),
        code_impact=DimensionScore(name="Code Impact", value=90),
        collaboration=DimensionScore(name="Collaboration", value=90),
        consistency=DimensionScore(name="Consistency", value=90),
    )
    result = AnalysisResult(
        repo="owner/repo",
        period_days=90,
        contributors=[r1, r2],
    )
    ranked = result.ranked_contributors
    assert ranked[0].username == "high"
    assert ranked[1].username == "low"
