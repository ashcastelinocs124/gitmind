# AI GitHub Analyzer — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python CLI that analyzes all GitHub repo contributors, scores them on 4 dimensions via heuristics, and generates OpenAI-powered summaries.

**Architecture:** Monolithic Python CLI with internal modules: models → fetcher → scorer → summarizer → reporter → cli. Each module is independently testable. TDD throughout.

**Tech Stack:** Python 3.11+, typer, PyGithub, rich, openai, pytest, dataclasses

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `github_analyzer/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "github-analyzer"
version = "0.1.0"
description = "Analyze GitHub contributors and grade developer effectiveness"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.9.0",
    "pygithub>=2.1.0",
    "rich>=13.0.0",
    "openai>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-mock>=3.0.0",
]

[project.scripts]
github-analyzer = "github_analyzer.cli:app"

[tool.setuptools.packages.find]
include = ["github_analyzer*"]
```

**Step 2: Create package init files**

`github_analyzer/__init__.py`:
```python
"""AI GitHub Analyzer — grade developer effectiveness from repo contributions."""
```

`tests/__init__.py`: empty file

`tests/conftest.py`:
```python
"""Shared test fixtures for github-analyzer."""
```

**Step 3: Install in dev mode and verify**

Run: `cd /Users/ash/Desktop/aigithubanalyzer && pip install -e ".[dev]"`
Expected: Successfully installed github-analyzer

**Step 4: Initialize git repo and commit**

```bash
git init
echo "__pycache__/\n*.egg-info/\n.env\ndist/\nbuild/\n*.pyc" > .gitignore
git add pyproject.toml github_analyzer/__init__.py tests/__init__.py tests/conftest.py .gitignore CLAUDE.md learnings.md memory.md docs/
git commit -m "chore: scaffold project with pyproject.toml and package structure"
```

---

### Task 2: Data Models

**Files:**
- Create: `github_analyzer/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing tests**

`tests/test_models.py`:
```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — cannot import from github_analyzer.models

**Step 3: Implement models.py**

`github_analyzer/models.py`:
```python
from dataclasses import dataclass, field
from typing import Any


def score_to_grade(score: float) -> str:
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B+"
    elif score >= 60:
        return "B"
    elif score >= 50:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


@dataclass
class DimensionScore:
    name: str
    value: float

    @property
    def clamped_value(self) -> float:
        return max(0, min(100, self.value))


@dataclass
class CommitData:
    sha: str
    message: str
    date: str
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0
    author: str = ""


@dataclass
class PullRequestData:
    number: int
    title: str
    author: str
    state: str  # "open", "closed", "merged"
    created_at: str
    merged: bool = False
    review_comments: int = 0
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0


@dataclass
class ReviewData:
    pr_number: int
    reviewer: str
    state: str  # "APPROVED", "CHANGES_REQUESTED", "COMMENTED"
    submitted_at: str
    body: str = ""


@dataclass
class IssueData:
    number: int
    title: str
    author: str
    state: str
    created_at: str
    comments: int = 0


@dataclass
class ContributorStats:
    username: str
    total_commits: int = 0
    total_prs: int = 0
    total_reviews: int = 0
    total_issues: int = 0
    commits: list[CommitData] = field(default_factory=list)
    pull_requests: list[PullRequestData] = field(default_factory=list)
    reviews: list[ReviewData] = field(default_factory=list)
    issues: list[IssueData] = field(default_factory=list)


@dataclass
class ContributorReport:
    username: str
    commit_quality: DimensionScore
    code_impact: DimensionScore
    collaboration: DimensionScore
    consistency: DimensionScore
    summary: str = ""
    headline: str = ""

    @property
    def overall_score(self) -> float:
        return (
            self.commit_quality.clamped_value * 0.25
            + self.code_impact.clamped_value * 0.30
            + self.collaboration.clamped_value * 0.25
            + self.consistency.clamped_value * 0.20
        )

    @property
    def overall_grade(self) -> str:
        return score_to_grade(self.overall_score)


@dataclass
class AnalysisResult:
    repo: str
    period_days: int
    contributors: list[ContributorReport] = field(default_factory=list)

    @property
    def ranked_contributors(self) -> list[ContributorReport]:
        return sorted(self.contributors, key=lambda c: c.overall_score, reverse=True)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add github_analyzer/models.py tests/test_models.py
git commit -m "feat: add data models for contributors, scores, and analysis results"
```

---

### Task 3: GitHub Data Fetcher

**Files:**
- Create: `github_analyzer/fetcher.py`
- Create: `tests/test_fetcher.py`

**Step 1: Write failing tests**

`tests/test_fetcher.py`:
```python
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timezone, timedelta
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_fetcher.py -v`
Expected: FAIL — cannot import GitHubFetcher

**Step 3: Implement fetcher.py**

`github_analyzer/fetcher.py`:
```python
from datetime import datetime, timezone, timedelta
from github import Github
from github_analyzer.models import (
    ContributorStats,
    CommitData,
    PullRequestData,
    ReviewData,
    IssueData,
)


class GitHubFetcher:
    def __init__(self, token: str):
        self.github = Github(token)

    def fetch(self, repo_name: str, days: int = 90) -> dict[str, ContributorStats]:
        repo = self.github.get_repo(repo_name)
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stats: dict[str, ContributorStats] = {}

        self._fetch_commits(repo, since, stats)
        self._fetch_pull_requests(repo, since, stats)
        self._fetch_issues(repo, since, stats)

        return stats

    def _get_or_create(self, stats: dict[str, ContributorStats], username: str) -> ContributorStats:
        if username not in stats:
            stats[username] = ContributorStats(username=username)
        return stats[username]

    def _fetch_commits(self, repo, since, stats):
        for commit in repo.get_commits(since=since):
            if not commit.author:
                continue
            login = commit.author.login
            contributor = self._get_or_create(stats, login)
            contributor.commits.append(
                CommitData(
                    sha=commit.sha,
                    message=commit.commit.message,
                    date=commit.commit.author.date.isoformat(),
                    additions=commit.stats.additions,
                    deletions=commit.stats.deletions,
                    files_changed=len(commit.files),
                    author=login,
                )
            )
            contributor.total_commits += 1

    def _fetch_pull_requests(self, repo, since, stats):
        for pr in repo.get_pulls(state="all", sort="created", direction="desc"):
            if pr.created_at < since:
                break
            login = pr.user.login
            contributor = self._get_or_create(stats, login)
            contributor.pull_requests.append(
                PullRequestData(
                    number=pr.number,
                    title=pr.title,
                    author=login,
                    state=pr.state,
                    created_at=pr.created_at.isoformat(),
                    merged=pr.merged,
                    review_comments=pr.review_comments,
                    additions=pr.additions,
                    deletions=pr.deletions,
                    files_changed=pr.changed_files,
                )
            )
            contributor.total_prs += 1

            # Collect reviews
            for review in pr.get_reviews():
                reviewer = review.user.login
                rev_contributor = self._get_or_create(stats, reviewer)
                rev_contributor.reviews.append(
                    ReviewData(
                        pr_number=pr.number,
                        reviewer=reviewer,
                        state=review.state,
                        submitted_at=review.submitted_at.isoformat(),
                        body=review.body or "",
                    )
                )
                rev_contributor.total_reviews += 1

    def _fetch_issues(self, repo, since, stats):
        for issue in repo.get_issues(state="all", since=since, sort="created", direction="desc"):
            if issue.pull_request is not None:
                continue
            login = issue.user.login
            contributor = self._get_or_create(stats, login)
            contributor.issues.append(
                IssueData(
                    number=issue.number,
                    title=issue.title,
                    author=login,
                    state=issue.state,
                    created_at=issue.created_at.isoformat(),
                    comments=issue.comments,
                )
            )
            contributor.total_issues += 1
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_fetcher.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add github_analyzer/fetcher.py tests/test_fetcher.py
git commit -m "feat: add GitHub data fetcher with commit, PR, issue, and review collection"
```

---

### Task 4: Scorer — Commit Quality

**Files:**
- Create: `github_analyzer/scorer.py`
- Create: `tests/test_scorer.py`

**Step 1: Write failing tests**

`tests/test_scorer.py`:
```python
from github_analyzer.scorer import (
    score_commit_quality,
    score_code_impact,
    score_collaboration,
    score_consistency,
    score_contributor,
)
from github_analyzer.models import ContributorStats, CommitData, PullRequestData, ReviewData, IssueData


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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_scorer.py::test_commit_quality_good_commits tests/test_scorer.py::test_commit_quality_bad_commits tests/test_scorer.py::test_commit_quality_no_commits -v`
Expected: FAIL — cannot import from scorer

**Step 3: Implement score_commit_quality in scorer.py**

`github_analyzer/scorer.py`:
```python
import statistics
from github_analyzer.models import ContributorStats, DimensionScore, ContributorReport


def score_commit_quality(stats: ContributorStats) -> DimensionScore:
    if not stats.commits:
        return DimensionScore(name="Commit Quality", value=0)

    message_scores = []
    size_scores = []
    churn_scores = []

    for commit in stats.commits:
        # Message quality: length and descriptiveness
        msg_len = len(commit.message.split('\n')[0])  # First line only
        if msg_len >= 30:
            message_scores.append(100)
        elif msg_len >= 15:
            message_scores.append(70)
        elif msg_len >= 7:
            message_scores.append(40)
        else:
            message_scores.append(10)

        # Commit size: penalize very large commits
        total_changes = commit.additions + commit.deletions
        if total_changes == 0:
            size_scores.append(50)
        elif total_changes <= 50:
            size_scores.append(100)
        elif total_changes <= 200:
            size_scores.append(80)
        elif total_changes <= 500:
            size_scores.append(60)
        elif total_changes <= 1000:
            size_scores.append(30)
        else:
            size_scores.append(10)

        # Add/delete balance: reward refactoring (has both adds and deletes)
        if commit.additions > 0 and commit.deletions > 0:
            ratio = min(commit.additions, commit.deletions) / max(commit.additions, commit.deletions)
            churn_scores.append(50 + ratio * 50)  # 50-100 range
        else:
            churn_scores.append(30)  # Pure additions or deletions

    avg_message = statistics.mean(message_scores)
    avg_size = statistics.mean(size_scores)
    avg_churn = statistics.mean(churn_scores)

    # Weight: message 40%, size 40%, churn 20%
    final = avg_message * 0.4 + avg_size * 0.4 + avg_churn * 0.2
    return DimensionScore(name="Commit Quality", value=round(final, 1))
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_scorer.py::test_commit_quality_good_commits tests/test_scorer.py::test_commit_quality_bad_commits tests/test_scorer.py::test_commit_quality_no_commits -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add github_analyzer/scorer.py tests/test_scorer.py
git commit -m "feat: add commit quality scoring with message, size, and churn analysis"
```

---

### Task 5: Scorer — Code Impact

**Files:**
- Modify: `github_analyzer/scorer.py`
- Modify: `tests/test_scorer.py`

**Step 1: Add failing tests to test_scorer.py**

Append to `tests/test_scorer.py`:
```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_scorer.py::test_code_impact_high_impact -v`
Expected: FAIL

**Step 3: Add score_code_impact to scorer.py**

Append to `github_analyzer/scorer.py`:
```python
def score_code_impact(stats: ContributorStats, total_repo_commits: int = 1) -> DimensionScore:
    if not stats.commits:
        return DimensionScore(name="Code Impact", value=0)

    # Net lines contributed
    total_additions = sum(c.additions for c in stats.commits)
    total_deletions = sum(c.deletions for c in stats.commits)
    net_lines = total_additions - total_deletions

    # Lines score: reward meaningful net contributions
    if net_lines > 500:
        lines_score = 100
    elif net_lines > 200:
        lines_score = 80
    elif net_lines > 50:
        lines_score = 60
    elif net_lines > 0:
        lines_score = 40
    else:
        lines_score = 20  # Net negative is still valuable (cleanup)

    # Commit share: what fraction of total repo commits are theirs
    commit_share = stats.total_commits / max(total_repo_commits, 1)
    share_score = min(100, commit_share * 200)  # 50% of commits = 100

    # Files breadth: how many files they touch on average
    avg_files = statistics.mean([c.files_changed for c in stats.commits])
    if avg_files >= 5:
        breadth_score = 90
    elif avg_files >= 3:
        breadth_score = 70
    elif avg_files >= 2:
        breadth_score = 50
    else:
        breadth_score = 30

    # Merged PR bonus
    merged_prs = sum(1 for pr in stats.pull_requests if pr.merged)
    pr_bonus = min(20, merged_prs * 5)

    final = lines_score * 0.3 + share_score * 0.3 + breadth_score * 0.2 + pr_bonus + 10  # base 10
    final = min(100, final)
    return DimensionScore(name="Code Impact", value=round(final, 1))
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_scorer.py -k "code_impact" -v`
Expected: All 3 PASS

**Step 5: Commit**

```bash
git add github_analyzer/scorer.py tests/test_scorer.py
git commit -m "feat: add code impact scoring with lines, commit share, and breadth analysis"
```

---

### Task 6: Scorer — Collaboration

**Files:**
- Modify: `github_analyzer/scorer.py`
- Modify: `tests/test_scorer.py`

**Step 1: Add failing tests**

Append to `tests/test_scorer.py`:
```python
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
```

**Step 2: Run to verify failure**

Run: `pytest tests/test_scorer.py -k "collaboration" -v`
Expected: FAIL

**Step 3: Implement score_collaboration**

Append to `github_analyzer/scorer.py`:
```python
def score_collaboration(stats: ContributorStats) -> DimensionScore:
    if not stats.reviews and not stats.issues and not stats.pull_requests:
        return DimensionScore(name="Collaboration", value=0)

    # Reviews given score
    if stats.total_reviews >= 10:
        review_score = 100
    elif stats.total_reviews >= 5:
        review_score = 80
    elif stats.total_reviews >= 2:
        review_score = 60
    elif stats.total_reviews >= 1:
        review_score = 40
    else:
        review_score = 0

    # Issue participation
    if stats.total_issues >= 5:
        issue_score = 100
    elif stats.total_issues >= 3:
        issue_score = 70
    elif stats.total_issues >= 1:
        issue_score = 40
    else:
        issue_score = 0

    # PR merge rate
    if stats.total_prs > 0:
        merged = sum(1 for pr in stats.pull_requests if pr.merged)
        merge_rate = merged / stats.total_prs
        pr_score = merge_rate * 100
    else:
        pr_score = 0

    # Weight: reviews 50%, issues 20%, PR merge rate 30%
    final = review_score * 0.5 + issue_score * 0.2 + pr_score * 0.3
    return DimensionScore(name="Collaboration", value=round(final, 1))
```

**Step 4: Run tests**

Run: `pytest tests/test_scorer.py -k "collaboration" -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add github_analyzer/scorer.py tests/test_scorer.py
git commit -m "feat: add collaboration scoring with review, issue, and PR merge analysis"
```

---

### Task 7: Scorer — Consistency & Patterns

**Files:**
- Modify: `github_analyzer/scorer.py`
- Modify: `tests/test_scorer.py`

**Step 1: Add failing tests**

Append to `tests/test_scorer.py`:
```python
from datetime import datetime, timedelta


def test_consistency_regular_commits():
    # Commits spread across multiple weeks
    base = datetime(2026, 1, 1)
    commits = [
        _make_commit(date=(base + timedelta(weeks=i)).isoformat())
        for i in range(12)
    ]
    stats = ContributorStats(username="alice", total_commits=12, commits=commits)
    score = score_consistency(stats, period_days=90)
    assert score.value >= 70, f"Regular commits should score >= 70, got {score.value}"


def test_consistency_sporadic_commits():
    # All commits in one day
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
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_scorer.py -k "consistency" -v`
Expected: FAIL

**Step 3: Implement score_consistency**

Append to `github_analyzer/scorer.py`:
```python
from datetime import datetime


def score_consistency(stats: ContributorStats, period_days: int = 90) -> DimensionScore:
    if not stats.commits:
        return DimensionScore(name="Consistency", value=0)

    # Parse commit dates into weeks
    weeks_active: set[int] = set()
    unique_dirs: set[str] = set()

    for commit in stats.commits:
        date_str = commit.date
        if isinstance(date_str, str):
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            dt = date_str
        week_num = dt.isocalendar()[1] + dt.year * 100
        weeks_active.add(week_num)

    total_weeks = max(period_days // 7, 1)
    active_ratio = len(weeks_active) / total_weeks

    # Active weeks score
    if active_ratio >= 0.8:
        regularity_score = 100
    elif active_ratio >= 0.5:
        regularity_score = 75
    elif active_ratio >= 0.3:
        regularity_score = 50
    elif active_ratio >= 0.1:
        regularity_score = 30
    else:
        regularity_score = 15

    # Commit spread: standard deviation of commits per week
    # Lower std dev relative to mean = more consistent
    if len(weeks_active) >= 2:
        week_counts: dict[int, int] = {}
        for commit in stats.commits:
            date_str = commit.date
            if isinstance(date_str, str):
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                dt = date_str
            wk = dt.isocalendar()[1] + dt.year * 100
            week_counts[wk] = week_counts.get(wk, 0) + 1

        values = list(week_counts.values())
        mean_commits = statistics.mean(values)
        if mean_commits > 0:
            cv = statistics.stdev(values) / mean_commits if len(values) > 1 else 0
            # Lower coefficient of variation = more consistent
            if cv < 0.3:
                spread_score = 100
            elif cv < 0.6:
                spread_score = 75
            elif cv < 1.0:
                spread_score = 50
            else:
                spread_score = 25
        else:
            spread_score = 0
    else:
        spread_score = 20

    # Weight: regularity 60%, spread 40%
    final = regularity_score * 0.6 + spread_score * 0.4
    return DimensionScore(name="Consistency", value=round(final, 1))
```

**Step 4: Run tests**

Run: `pytest tests/test_scorer.py -k "consistency" -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add github_analyzer/scorer.py tests/test_scorer.py
git commit -m "feat: add consistency scoring with regularity and commit spread analysis"
```

---

### Task 8: Scorer — Overall score_contributor Function

**Files:**
- Modify: `github_analyzer/scorer.py`
- Modify: `tests/test_scorer.py`

**Step 1: Add failing test**

Append to `tests/test_scorer.py`:
```python
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
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_scorer.py::test_score_contributor_returns_report -v`
Expected: FAIL

**Step 3: Implement score_contributor**

Append to `github_analyzer/scorer.py`:
```python
def score_contributor(
    stats: ContributorStats,
    total_repo_commits: int = 1,
    period_days: int = 90,
) -> ContributorReport:
    cq = score_commit_quality(stats)
    ci = score_code_impact(stats, total_repo_commits)
    co = score_collaboration(stats)
    cs = score_consistency(stats, period_days)

    return ContributorReport(
        username=stats.username,
        commit_quality=cq,
        code_impact=ci,
        collaboration=co,
        consistency=cs,
    )
```

**Step 4: Run all scorer tests**

Run: `pytest tests/test_scorer.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add github_analyzer/scorer.py tests/test_scorer.py
git commit -m "feat: add score_contributor function combining all four dimensions"
```

---

### Task 9: OpenAI Summarizer

**Files:**
- Create: `github_analyzer/summarizer.py`
- Create: `tests/test_summarizer.py`

**Step 1: Write failing tests**

`tests/test_summarizer.py`:
```python
from unittest.mock import patch, MagicMock
from github_analyzer.summarizer import generate_summaries
from github_analyzer.models import ContributorReport, DimensionScore


def _make_report(username, cq=70, ci=70, co=70, cs=70):
    return ContributorReport(
        username=username,
        commit_quality=DimensionScore(name="Commit Quality", value=cq),
        code_impact=DimensionScore(name="Code Impact", value=ci),
        collaboration=DimensionScore(name="Collaboration", value=co),
        consistency=DimensionScore(name="Consistency", value=cs),
    )


@patch("github_analyzer.summarizer.OpenAI")
def test_generate_summaries_populates_fields(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "HEADLINE: Strong all-around contributor\nSUMMARY: Alice demonstrates consistent commit quality and solid collaboration skills. Her code impact is above average with well-structured changes."
    mock_client.chat.completions.create.return_value = mock_response

    reports = [_make_report("alice", cq=85, ci=90, co=75, cs=80)]
    generate_summaries(reports, api_key="fake-key")

    assert reports[0].headline != ""
    assert reports[0].summary != ""
    mock_client.chat.completions.create.assert_called_once()


@patch("github_analyzer.summarizer.OpenAI")
def test_generate_summaries_handles_multiple_contributors(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "HEADLINE: Solid contributor\nSUMMARY: Good work overall."
    mock_client.chat.completions.create.return_value = mock_response

    reports = [_make_report("alice"), _make_report("bob")]
    generate_summaries(reports, api_key="fake-key")

    assert mock_client.chat.completions.create.call_count == 2
    assert all(r.summary != "" for r in reports)


def test_generate_summaries_skips_when_no_key():
    reports = [_make_report("alice")]
    generate_summaries(reports, api_key=None)
    assert reports[0].summary == ""
    assert reports[0].headline == ""
```

**Step 2: Run to verify failure**

Run: `pytest tests/test_summarizer.py -v`
Expected: FAIL — cannot import

**Step 3: Implement summarizer.py**

`github_analyzer/summarizer.py`:
```python
from openai import OpenAI
from github_analyzer.models import ContributorReport


def generate_summaries(reports: list[ContributorReport], api_key: str | None) -> None:
    if not api_key:
        return

    client = OpenAI(api_key=api_key)

    for report in reports:
        prompt = _build_prompt(report)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an engineering analyst. Given a developer's contribution metrics, provide a brief assessment. Respond in exactly this format:\nHEADLINE: <one-line characterization>\nSUMMARY: <2-3 sentence assessment of strengths and areas for improvement>"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )

        text = response.choices[0].message.content or ""
        _parse_response(report, text)


def _build_prompt(report: ContributorReport) -> str:
    return (
        f"Developer: {report.username}\n"
        f"Overall Grade: {report.overall_grade} ({report.overall_score:.1f}/100)\n"
        f"Commit Quality: {report.commit_quality.clamped_value:.0f}/100\n"
        f"Code Impact: {report.code_impact.clamped_value:.0f}/100\n"
        f"Collaboration: {report.collaboration.clamped_value:.0f}/100\n"
        f"Consistency: {report.consistency.clamped_value:.0f}/100\n"
    )


def _parse_response(report: ContributorReport, text: str) -> None:
    lines = text.strip().split("\n")
    for line in lines:
        if line.startswith("HEADLINE:"):
            report.headline = line.replace("HEADLINE:", "").strip()
        elif line.startswith("SUMMARY:"):
            report.summary = line.replace("SUMMARY:", "").strip()

    # Fallback if parsing fails
    if not report.headline:
        report.headline = text[:80] if text else ""
    if not report.summary:
        report.summary = text if text else ""
```

**Step 4: Run tests**

Run: `pytest tests/test_summarizer.py -v`
Expected: All 3 PASS

**Step 5: Commit**

```bash
git add github_analyzer/summarizer.py tests/test_summarizer.py
git commit -m "feat: add OpenAI-powered contributor summary generation"
```

---

### Task 10: Reporter — Terminal Output

**Files:**
- Create: `github_analyzer/reporter.py`
- Create: `tests/test_reporter.py`

**Step 1: Write failing tests**

`tests/test_reporter.py`:
```python
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
    # alice should have a high grade
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
```

**Step 2: Run to verify failure**

Run: `pytest tests/test_reporter.py -v`
Expected: FAIL

**Step 3: Implement reporter.py**

`github_analyzer/reporter.py`:
```python
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
```

**Step 4: Run tests**

Run: `pytest tests/test_reporter.py -v`
Expected: All 3 PASS

**Step 5: Commit**

```bash
git add github_analyzer/reporter.py tests/test_reporter.py
git commit -m "feat: add terminal and JSON report renderers"
```

---

### Task 11: CLI Entry Point

**Files:**
- Create: `github_analyzer/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write failing tests**

`tests/test_cli.py`:
```python
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from github_analyzer.cli import app
from github_analyzer.models import ContributorStats, CommitData

runner = CliRunner()


@patch("github_analyzer.cli.generate_summaries")
@patch("github_analyzer.cli.GitHubFetcher")
def test_cli_analyze_json_output(mock_fetcher_cls, mock_summarize):
    mock_fetcher = MagicMock()
    mock_fetcher_cls.return_value = mock_fetcher
    mock_fetcher.fetch.return_value = {
        "alice": ContributorStats(
            username="alice",
            total_commits=1,
            commits=[
                CommitData(sha="abc", message="feat: add feature", date="2026-03-01T12:00:00",
                           additions=50, deletions=10, files_changed=3, author="alice")
            ],
        )
    }

    result = runner.invoke(app, ["analyze", "owner/repo", "--token", "fake", "--json", "--no-ai"])
    assert result.exit_code == 0
    assert '"repo": "owner/repo"' in result.output
    assert '"alice"' in result.output


@patch("github_analyzer.cli.generate_summaries")
@patch("github_analyzer.cli.GitHubFetcher")
def test_cli_analyze_terminal_output(mock_fetcher_cls, mock_summarize):
    mock_fetcher = MagicMock()
    mock_fetcher_cls.return_value = mock_fetcher
    mock_fetcher.fetch.return_value = {
        "alice": ContributorStats(
            username="alice",
            total_commits=1,
            commits=[
                CommitData(sha="abc", message="feat: add feature", date="2026-03-01T12:00:00",
                           additions=50, deletions=10, files_changed=3, author="alice")
            ],
        )
    }

    result = runner.invoke(app, ["analyze", "owner/repo", "--token", "fake", "--no-ai"])
    assert result.exit_code == 0
    assert "alice" in result.output


@patch("github_analyzer.cli.GitHubFetcher")
def test_cli_requires_token(mock_fetcher_cls):
    # Unset env var to ensure no token available
    with patch.dict("os.environ", {}, clear=True):
        result = runner.invoke(app, ["analyze", "owner/repo"])
        assert result.exit_code != 0 or "token" in result.output.lower() or "GITHUB_TOKEN" in result.output
```

**Step 2: Run to verify failure**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL

**Step 3: Implement cli.py**

`github_analyzer/cli.py`:
```python
import os
import typer
from rich.console import Console
from github_analyzer.fetcher import GitHubFetcher
from github_analyzer.scorer import score_contributor
from github_analyzer.summarizer import generate_summaries
from github_analyzer.reporter import render_terminal, render_json
from github_analyzer.models import AnalysisResult

app = typer.Typer(help="AI GitHub Analyzer — grade developer effectiveness from repo contributions.")
console = Console()


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

    with console.status("[bold green]Fetching data from GitHub...") as status:
        fetcher = GitHubFetcher(token=token)
        contributor_stats = fetcher.fetch(repo_name, days=days)

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
            with console.status("[bold green]Generating AI summaries..."):
                generate_summaries(reports, api_key=api_key)
        else:
            console.print("[dim]Skipping AI summaries (OPENAI_API_KEY not set)[/dim]")

    result = AnalysisResult(repo=repo_name, period_days=days, contributors=reports)

    if json_output:
        print(render_json(result))
    else:
        print(render_terminal(result))


if __name__ == "__main__":
    app()
```

**Step 4: Run tests**

Run: `pytest tests/test_cli.py -v`
Expected: All 3 PASS

**Step 5: Run full test suite**

Run: `pytest -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add github_analyzer/cli.py tests/test_cli.py
git commit -m "feat: add CLI entry point with analyze command, JSON and terminal output"
```

---

### Task 12: End-to-End Smoke Test

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Verify the tool runs**

Run: `github-analyzer --help`
Expected: Shows help text with "analyze" command

Run: `github-analyzer analyze --help`
Expected: Shows analyze command options (--token, --days, --json, --no-ai)

**Step 2: Run full test suite one final time**

Run: `pytest -v --tb=short`
Expected: All tests PASS

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: finalize project setup and verify end-to-end"
```

---

## Summary of Tasks

| Task | Component | Description |
|------|-----------|-------------|
| 1 | Scaffolding | pyproject.toml, package structure, git init |
| 2 | Models | Data classes for contributors, scores, results |
| 3 | Fetcher | GitHub API data collection (commits, PRs, issues, reviews) |
| 4 | Scorer | Commit quality scoring |
| 5 | Scorer | Code impact scoring |
| 6 | Scorer | Collaboration scoring |
| 7 | Scorer | Consistency & patterns scoring |
| 8 | Scorer | Overall score_contributor combining all dimensions |
| 9 | Summarizer | OpenAI summary generation |
| 10 | Reporter | Terminal (rich) and JSON output |
| 11 | CLI | Typer entry point with flags |
| 12 | Smoke test | End-to-end verification |
