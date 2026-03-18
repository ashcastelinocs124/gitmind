"""Tests for GitHubFetcher — commit, PR, issue, and review collection."""

from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from github_analyzer.fetcher import GitHubFetcher
from github_analyzer.models import ContributorStats


def _make_mock_commit(sha, message, author_login, date, additions=10, deletions=5, files=None):
    commit = MagicMock()
    commit.sha = sha
    commit.commit.message = message
    commit.commit.author.date = date
    commit.author = MagicMock()
    commit.author.login = author_login
    commit.stats.additions = additions
    commit.stats.deletions = deletions
    commit.files = files or [MagicMock()]
    return commit


def _make_mock_pr(number, title, author_login, state, created_at, merged=False):
    pr = MagicMock()
    pr.number = number
    pr.title = title
    pr.user.login = author_login
    pr.state = state
    pr.created_at = created_at
    pr.merged = merged
    pr.review_comments = 2
    pr.additions = 50
    pr.deletions = 10
    pr.changed_files = 3
    return pr


def _make_mock_issue(number, title, author_login, state, created_at, comments=0):
    issue = MagicMock()
    issue.number = number
    issue.title = title
    issue.user.login = author_login
    issue.state = state
    issue.created_at = created_at
    issue.comments = comments
    issue.pull_request = None  # Not a PR
    return issue


def _make_mock_review(pr_number, reviewer_login, state, submitted_at):
    review = MagicMock()
    review.user.login = reviewer_login
    review.state = state
    review.submitted_at = submitted_at
    review.body = "Looks good"
    return review


@patch("github_analyzer.fetcher.Github")
def test_fetcher_collects_commits(mock_github_cls):
    mock_repo = MagicMock()
    mock_github_cls.return_value.get_repo.return_value = mock_repo

    now = datetime.now(timezone.utc)
    mock_commit = _make_mock_commit("abc123", "fix bug", "alice", now)
    mock_repo.get_commits.return_value = [mock_commit]
    mock_repo.get_pulls.return_value = []
    mock_repo.get_issues.return_value = []

    fetcher = GitHubFetcher(token="fake-token")
    stats = fetcher.fetch("owner/repo", days=90)

    assert "alice" in stats
    assert stats["alice"].total_commits == 1
    assert stats["alice"].commits[0].sha == "abc123"


@patch("github_analyzer.fetcher.Github")
def test_fetcher_collects_prs(mock_github_cls):
    mock_repo = MagicMock()
    mock_github_cls.return_value.get_repo.return_value = mock_repo

    now = datetime.now(timezone.utc)
    mock_repo.get_commits.return_value = []
    mock_pr = _make_mock_pr(1, "Add feature", "bob", "closed", now, merged=True)
    mock_repo.get_pulls.return_value = [mock_pr]
    mock_repo.get_issues.return_value = []

    # Mock reviews on the PR
    mock_review = _make_mock_review(1, "alice", "APPROVED", now)
    mock_pr.get_reviews.return_value = [mock_review]

    fetcher = GitHubFetcher(token="fake-token")
    stats = fetcher.fetch("owner/repo", days=90)

    assert "bob" in stats
    assert stats["bob"].total_prs == 1
    assert "alice" in stats
    assert stats["alice"].total_reviews == 1


@patch("github_analyzer.fetcher.Github")
def test_fetcher_collects_issues(mock_github_cls):
    mock_repo = MagicMock()
    mock_github_cls.return_value.get_repo.return_value = mock_repo

    now = datetime.now(timezone.utc)
    mock_repo.get_commits.return_value = []
    mock_repo.get_pulls.return_value = []
    mock_issue = _make_mock_issue(10, "Bug report", "charlie", "open", now, comments=3)
    mock_repo.get_issues.return_value = [mock_issue]

    fetcher = GitHubFetcher(token="fake-token")
    stats = fetcher.fetch("owner/repo", days=90)

    assert "charlie" in stats
    assert stats["charlie"].total_issues == 1
    assert stats["charlie"].issues[0].comments == 3


@patch("github_analyzer.fetcher.Github")
def test_fetcher_skips_prs_in_issues(mock_github_cls):
    mock_repo = MagicMock()
    mock_github_cls.return_value.get_repo.return_value = mock_repo

    now = datetime.now(timezone.utc)
    mock_repo.get_commits.return_value = []
    mock_repo.get_pulls.return_value = []

    # Issue that is actually a PR (has pull_request attribute)
    mock_issue = _make_mock_issue(10, "PR title", "charlie", "open", now)
    mock_issue.pull_request = MagicMock()  # Not None = this is a PR
    mock_repo.get_issues.return_value = [mock_issue]

    fetcher = GitHubFetcher(token="fake-token")
    stats = fetcher.fetch("owner/repo", days=90)

    assert "charlie" not in stats or stats.get("charlie", ContributorStats("")).total_issues == 0
