"""Scoring engine for GitHub contributor analysis.

Provides four dimension-level scoring functions and an overall contributor scorer:
- score_commit_quality: Evaluates commit message quality, size discipline, and churn balance
- score_code_impact: Measures lines contributed, commit share, file breadth, and PR merges
- score_collaboration: Assesses review activity, issue participation, and PR merge rate
- score_consistency: Gauges regularity of contributions over time
- score_contributor: Combines all dimensions into a ContributorReport
"""

import statistics
from datetime import datetime
from github_analyzer.models import ContributorStats, DimensionScore, ContributorReport


def score_commit_quality(stats: ContributorStats) -> DimensionScore:
    """Score the quality of a contributor's commits.

    Evaluates three sub-dimensions:
    - Message quality (40%): length and descriptiveness of commit message first line
    - Commit size (40%): penalizes very large commits, rewards focused changes
    - Churn balance (20%): rewards commits with both additions and deletions (refactoring)

    Returns a DimensionScore with value 0 if no commits exist.
    """
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


def score_code_impact(stats: ContributorStats, total_repo_commits: int = 1) -> DimensionScore:
    """Score the code impact of a contributor.

    Evaluates four sub-dimensions:
    - Net lines contributed (30%): rewards meaningful net additions
    - Commit share (30%): fraction of total repo commits attributed to this contributor
    - File breadth (20%): average number of files touched per commit
    - Merged PR bonus (flat): up to 20 points for merged pull requests

    A base of 10 points is added. Final score is clamped to [0, 100].
    Returns a DimensionScore with value 0 if no commits exist.
    """
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
    if avg_files >= 4:
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


def score_collaboration(stats: ContributorStats) -> DimensionScore:
    """Score a contributor's collaboration activity.

    Evaluates three sub-dimensions:
    - Reviews given (50%): number of code reviews submitted
    - Issue participation (20%): number of issues created or contributed to
    - PR merge rate (30%): fraction of the contributor's PRs that were merged

    Returns a DimensionScore with value 0 if no reviews, issues, or PRs exist.
    """
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


def score_consistency(stats: ContributorStats, period_days: int = 90) -> DimensionScore:
    """Score the consistency of a contributor's activity over time.

    Evaluates two sub-dimensions:
    - Regularity (60%): ratio of weeks with at least one commit to total weeks in period
    - Spread (40%): evenness of commit distribution across active weeks (via CV)

    Returns a DimensionScore with value 0 if no commits exist.
    """
    if not stats.commits:
        return DimensionScore(name="Consistency", value=0)

    # Parse commit dates into weeks
    weeks_active: set[int] = set()

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


def score_contributor(
    stats: ContributorStats,
    total_repo_commits: int = 1,
    period_days: int = 90,
) -> ContributorReport:
    """Score a contributor across all four dimensions and return a full report.

    Delegates to the four dimension scorers and assembles a ContributorReport
    whose overall_score and overall_grade properties combine them with weights:
    Commit Quality 25%, Code Impact 30%, Collaboration 25%, Consistency 20%.
    """
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
