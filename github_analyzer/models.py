"""Data models for GitHub contributor analysis.

Defines the core data structures used throughout the analyzer:
- Raw data containers (CommitData, PullRequestData, ReviewData, IssueData)
- Aggregated contributor statistics (ContributorStats)
- Scored results (DimensionScore, ContributorReport, AnalysisResult)
- Grade conversion utility (score_to_grade)
"""

from dataclasses import dataclass, field


def score_to_grade(score: float) -> str:
    """Convert a numeric score (0-100) to a letter grade.

    Grade thresholds:
        90+ -> A+, 80+ -> A, 70+ -> B+, 60+ -> B,
        50+ -> C,  40+ -> D, <40 -> F
    """
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
    """A single scoring dimension (e.g. Commit Quality) with a name and value."""

    name: str
    value: float

    @property
    def clamped_value(self) -> float:
        """Return value clamped to [0, 100]."""
        return max(0, min(100, self.value))


@dataclass
class CommitData:
    """Raw data for a single commit."""

    sha: str
    message: str
    date: str
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0
    author: str = ""


@dataclass
class PullRequestData:
    """Raw data for a single pull request."""

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
    """Raw data for a single code review."""

    pr_number: int
    reviewer: str
    state: str  # "APPROVED", "CHANGES_REQUESTED", "COMMENTED"
    submitted_at: str
    body: str = ""


@dataclass
class IssueData:
    """Raw data for a single issue."""

    number: int
    title: str
    author: str
    state: str
    created_at: str
    comments: int = 0


@dataclass
class ContributorStats:
    """Aggregated raw statistics for a single contributor."""

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
    """Scored report for a single contributor across all dimensions."""

    username: str
    commit_quality: DimensionScore
    code_impact: DimensionScore
    collaboration: DimensionScore
    consistency: DimensionScore
    summary: str = ""
    headline: str = ""

    @property
    def overall_score(self) -> float:
        """Weighted overall score across all dimensions.

        Weights: Commit Quality 25%, Code Impact 30%,
                 Collaboration 25%, Consistency 20%.
        """
        return (
            self.commit_quality.clamped_value * 0.25
            + self.code_impact.clamped_value * 0.30
            + self.collaboration.clamped_value * 0.25
            + self.consistency.clamped_value * 0.20
        )

    @property
    def overall_grade(self) -> str:
        """Letter grade derived from overall_score."""
        return score_to_grade(self.overall_score)


@dataclass
class AnalysisResult:
    """Complete analysis result for a repository."""

    repo: str
    period_days: int
    contributors: list[ContributorReport] = field(default_factory=list)

    @property
    def ranked_contributors(self) -> list[ContributorReport]:
        """Contributors sorted by overall_score, highest first."""
        return sorted(
            self.contributors, key=lambda c: c.overall_score, reverse=True
        )
