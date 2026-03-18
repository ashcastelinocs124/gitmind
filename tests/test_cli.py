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
