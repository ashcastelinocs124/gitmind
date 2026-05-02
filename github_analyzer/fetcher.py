"""GitHub data fetcher for contributor analysis.

Uses PyGithub to collect commits, pull requests, issues, and code reviews
from a repository, aggregating them into per-contributor statistics.
"""

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
    """Fetches and aggregates contributor activity from a GitHub repository.

    Args:
        token: A GitHub personal access token for API authentication.
    """

    def __init__(self, token: str):
        self.github = Github(token)

    def fetch(self, repo_name: str, days: int = 90) -> dict[str, ContributorStats]:
        """Fetch contributor statistics for a repository.

        Collects commits, pull requests (with reviews), and issues created
        within the specified time window, returning per-contributor aggregates.

        Args:
            repo_name: Repository in "owner/repo" format.
            days: Number of days to look back (default 90).

        Returns:
            Dictionary mapping GitHub username to their ContributorStats.
        """
        repo = self.github.get_repo(repo_name)
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stats: dict[str, ContributorStats] = {}

        self._fetch_commits(repo, since, stats)
        self._fetch_pull_requests(repo, since, stats)
        self._fetch_issues(repo, since, stats)

        return stats

    def _get_or_create(
        self, stats: dict[str, ContributorStats], username: str
    ) -> ContributorStats:
        """Return existing ContributorStats for username, or create a new one."""
        if username not in stats:
            stats[username] = ContributorStats(username=username)
        return stats[username]

    def _fetch_commits(self, repo, since, stats):
        """Collect commits since the cutoff date into per-author stats."""
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
                    files_changed=len(list(commit.files)),
                    author=login,
                )
            )
            contributor.total_commits += 1

    def _fetch_pull_requests(self, repo, since, stats):
        """Collect pull requests and their reviews since the cutoff date."""
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

            # Collect reviews on this PR
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
        """Collect issues (excluding PRs) since the cutoff date."""
        for issue in repo.get_issues(
            state="all", since=since, sort="created", direction="desc"
        ):
            # GitHub's issue API includes pull requests; skip them
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
