"""OpenAI-powered contributor summary generation.

Uses GPT-4o to produce a one-line headline and a 2-3 sentence summary
for each contributor based on their scored metrics.  When no API key is
provided the function is a no-op, leaving the report fields at their
default empty strings.
"""

from openai import OpenAI
from github_analyzer.models import ContributorReport


def generate_summaries(reports: list[ContributorReport], api_key: str | None) -> None:
    """Populate *headline* and *summary* on each report using OpenAI.

    Args:
        reports: Scored contributor reports to enrich with AI summaries.
        api_key: OpenAI API key.  If ``None`` or empty, the function
                 returns immediately without modifying reports.
    """
    if not api_key:
        return

    client = OpenAI(api_key=api_key)

    for report in reports:
        prompt = _build_prompt(report)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an engineering analyst. Given a developer's "
                        "contribution metrics, provide a brief assessment. "
                        "Respond in exactly this format:\n"
                        "HEADLINE: <one-line characterization>\n"
                        "SUMMARY: <2-3 sentence assessment of strengths and "
                        "areas for improvement>"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )

        text = response.choices[0].message.content or ""
        _parse_response(report, text)


def _build_prompt(report: ContributorReport) -> str:
    """Build the user-message prompt from a scored report."""
    return (
        f"Developer: {report.username}\n"
        f"Overall Grade: {report.overall_grade} ({report.overall_score:.1f}/100)\n"
        f"Commit Quality: {report.commit_quality.clamped_value:.0f}/100\n"
        f"Code Impact: {report.code_impact.clamped_value:.0f}/100\n"
        f"Collaboration: {report.collaboration.clamped_value:.0f}/100\n"
        f"Consistency: {report.consistency.clamped_value:.0f}/100\n"
    )


def _parse_response(report: ContributorReport, text: str) -> None:
    """Parse the structured HEADLINE/SUMMARY response into report fields."""
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
