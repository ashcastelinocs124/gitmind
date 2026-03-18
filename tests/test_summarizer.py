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
