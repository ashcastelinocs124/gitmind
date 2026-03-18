import statistics
from datetime import datetime, timedelta
from github_analyzer.scorer import (
    score_commit_quality,
    score_code_impact,
    score_collaboration,
    score_consistency,
    score_contributor,
)
from github_analyzer.models import (
    ContributorStats, CommitData, PullRequestData, ReviewData, IssueData, DimensionScore,
)


def _make_commit(message="fix: resolve login bug", additions=20, deletions=5, files=3, date="2026-03-10T12:00:00"):
    return CommitData(
        sha="abc123",
        message=message,
        date=date,
        additions=additions,
        deletions=deletions,
        files_changed=files,
        author="alice",
    )


# --- Commit Quality ---

def test_commit_quality_good_commits():
    commits = [
        _make_commit(message="feat: add user authentication with JWT tokens", additions=50, deletions=10, files=4),
        _make_commit(message="fix: resolve race condition in session handler", additions=15, deletions=8, files=2),
        _make_commit(message="refactor: extract validation logic into helper", additions=30, deletions=25, files=3),
    ]
    stats = ContributorStats(username="alice", total_commits=3, commits=commits)
    score = score_commit_quality(stats)
    assert score.value >= 70, f"Good commits should score >= 70, got {score.value}"


def test_commit_quality_bad_commits():
    commits = [
        _make_commit(message="fix", additions=2000, deletions=0, files=50),
        _make_commit(message="wip", additions=1, deletions=0, files=1),
        _make_commit(message=".", additions=5000, deletions=3000, files=100),
    ]
    stats = ContributorStats(username="bob", total_commits=3, commits=commits)
    score = score_commit_quality(stats)
    assert score.value < 50, f"Bad commits should score < 50, got {score.value}"


def test_commit_quality_no_commits():
    stats = ContributorStats(username="ghost", total_commits=0, commits=[])
    score = score_commit_quality(stats)
    assert score.value == 0


# --- Code Impact ---

def test_code_impact_high_impact():
    commits = [
        _make_commit(additions=100, deletions=20, files=5),
        _make_commit(additions=80, deletions=30, files=4),
    ]
    prs = [
        PullRequestData(number=1, title="Big feature", author="alice", state="closed",
                        created_at="2026-03-10", merged=True, additions=100, deletions=20, files_changed=5),
    ]
    stats = ContributorStats(username="alice", total_commits=2, commits=commits,
                             total_prs=1, pull_requests=prs)
    score = score_code_impact(stats, total_repo_commits=10)
    assert score.value >= 60, f"High impact should score >= 60, got {score.value}"


def test_code_impact_low_impact():
    commits = [
        _make_commit(additions=2, deletions=0, files=1, message="update readme"),
    ]
    stats = ContributorStats(username="bob", total_commits=1, commits=commits)
    score = score_code_impact(stats, total_repo_commits=100)
    assert score.value < 50, f"Low impact should score < 50, got {score.value}"


def test_code_impact_no_commits():
    stats = ContributorStats(username="ghost")
    score = score_code_impact(stats, total_repo_commits=100)
    assert score.value == 0


# --- Collaboration ---

def test_collaboration_active_reviewer():
    reviews = [
        ReviewData(pr_number=1, reviewer="alice", state="APPROVED", submitted_at="2026-03-10T12:00:00"),
        ReviewData(pr_number=2, reviewer="alice", state="CHANGES_REQUESTED", submitted_at="2026-03-11T12:00:00"),
        ReviewData(pr_number=3, reviewer="alice", state="APPROVED", submitted_at="2026-03-12T12:00:00"),
    ]
    issues = [
        IssueData(number=1, title="Bug", author="alice", state="closed", created_at="2026-03-10", comments=2),
    ]
    prs = [
        PullRequestData(number=10, title="My PR", author="alice", state="closed",
                        created_at="2026-03-10", merged=True, additions=50, deletions=10, files_changed=3),
    ]
    stats = ContributorStats(
        username="alice", total_reviews=3, reviews=reviews,
        total_issues=1, issues=issues, total_prs=1, pull_requests=prs,
    )
    score = score_collaboration(stats)
    assert score.value >= 60, f"Active reviewer should score >= 60, got {score.value}"


def test_collaboration_no_activity():
    stats = ContributorStats(username="ghost")
    score = score_collaboration(stats)
    assert score.value == 0


# --- Consistency ---

def test_consistency_regular_commits():
    base = datetime(2026, 1, 1)
    commits = [
        _make_commit(date=(base + timedelta(weeks=i)).isoformat())
        for i in range(12)
    ]
    stats = ContributorStats(username="alice", total_commits=12, commits=commits)
    score = score_consistency(stats, period_days=90)
    assert score.value >= 70, f"Regular commits should score >= 70, got {score.value}"


def test_consistency_sporadic_commits():
    commits = [
        _make_commit(date="2026-03-01T12:00:00"),
        _make_commit(date="2026-03-01T13:00:00"),
        _make_commit(date="2026-03-01T14:00:00"),
    ]
    stats = ContributorStats(username="bob", total_commits=3, commits=commits)
    score = score_consistency(stats, period_days=90)
    assert score.value < 50, f"Sporadic commits should score < 50, got {score.value}"


def test_consistency_no_commits():
    stats = ContributorStats(username="ghost")
    score = score_consistency(stats, period_days=90)
    assert score.value == 0


# --- Overall score_contributor ---

def test_score_contributor_returns_report():
    commits = [
        _make_commit(message="feat: add login page", additions=50, deletions=10, files=3,
                     date="2026-03-01T12:00:00"),
        _make_commit(message="fix: resolve auth bug", additions=20, deletions=5, files=2,
                     date="2026-03-08T12:00:00"),
    ]
    reviews = [
        ReviewData(pr_number=1, reviewer="alice", state="APPROVED", submitted_at="2026-03-10T12:00:00"),
    ]
    stats = ContributorStats(
        username="alice", total_commits=2, commits=commits,
        total_reviews=1, reviews=reviews,
    )
    report = score_contributor(stats, total_repo_commits=10, period_days=90)
    assert report.username == "alice"
    assert 0 <= report.overall_score <= 100
    assert report.overall_grade in ("A+", "A", "B+", "B", "C", "D", "F")
