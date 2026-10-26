from pathlib import Path

from joblens.report import build_report


ROOT = Path(__file__).parents[1]
SAMPLES = ROOT / "samples" / "jobs"
SKILLS = ROOT / "samples" / "my_skills.example.txt"


def test_report_sections_chart_and_relative_paths(tmp_path: Path) -> None:
    output = tmp_path / "report.md"
    report = build_report(SAMPLES, SKILLS, output_path=output)

    for heading in (
        "## Overview",
        "## Top skills",
        "## Group comparisons",
        "## Your match",
        "## Limitations",
        "## Reproduce",
    ):
        assert heading in report
    assert (tmp_path / "report.png").exists()
    assert str(ROOT) not in report


def test_report_omits_match_without_personal_skills(tmp_path: Path) -> None:
    report = build_report(SAMPLES, output_path=tmp_path / "report.md")

    assert "## Your match" not in report
    assert "## Overview" in report
