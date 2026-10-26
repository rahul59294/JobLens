"""Generate Markdown reports and charts from local job postings."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPL_IGNORE_SYSTEM_FONTS", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .ingest import load_postings
from .match import load_my_skills, match_postings
from .skills import load_catalog, skill_counts
from .stats import compare


def _relative(path: str | Path) -> str:
    return Path(os.path.relpath(Path(path), Path.cwd())).as_posix()


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _value_counts(postings: pd.DataFrame, field: str) -> list[list[str]]:
    counts = postings[field].fillna("Unknown").replace("", "Unknown").value_counts()
    return [[str(value), str(int(count))] for value, count in counts.items()]


def _format_comparisons(postings: pd.DataFrame, by: str, catalog: Path) -> list[str]:
    results = compare(postings, by, catalog)
    lines = [f"### By {by}"]
    if results.empty:
        return lines + ["No skills were mentioned in at least 2 postings."]
    if bool(results["small_sample"].any()):
        lines.append("> **Warning:** one or more groups contain fewer than 5 postings.")
    rows = [
        [
            str(row["skill"]),
            str(row["group"]),
            f"{row['odds_ratio']:.2f}",
            f"{row['p_value']:.4g}",
            f"{row['p_adjusted']:.4g}",
            str(row["method"]),
        ]
        for _, row in results.iterrows()
    ]
    return lines + [
        _markdown_table(
            ["Skill", "Group", "Odds ratio", "p-value", "BH-adjusted p", "Method"], rows
        )
    ]


def _save_skill_chart(counts: pd.DataFrame, chart_path: Path) -> None:
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    chart_data = counts.head(20).sort_values("count")
    fig, axis = plt.subplots(figsize=(9, max(4, len(chart_data) * 0.3)))
    if not chart_data.empty:
        y = range(len(chart_data))
        errors = [
            (chart_data["count"] - chart_data["ci_low"] * chart_data["count"] / chart_data["share"]),
            (chart_data["ci_high"] * chart_data["count"] / chart_data["share"] - chart_data["count"]),
        ]
        axis.barh(list(y), chart_data["count"], xerr=errors, capsize=3, color="#4472c4")
        axis.set_yticks(list(y), chart_data["skill"])
    axis.set_xlabel("Postings mentioning skill")
    axis.set_title("Top skills in job postings")
    fig.tight_layout()
    fig.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def build_report(
    folder: str | Path,
    skills_path: str | Path | None = None,
    cv_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> str:
    """Build a Markdown report and save its adjacent top-skills PNG chart."""

    if skills_path is not None and cv_path is not None:
        raise ValueError("provide at most one of skills_path or cv_path")

    output = Path(output_path or "report.md")
    chart_path = output.with_suffix(".png")
    output.parent.mkdir(parents=True, exist_ok=True)
    postings = load_postings(folder)
    catalog_path = Path("data/skills.csv")
    catalog = load_catalog(catalog_path)
    counts = skill_counts(postings, catalog)
    _save_skill_chart(counts, chart_path)

    overview = [
        "## Overview",
        f"{len(postings)} postings analyzed.",
        "",
        _markdown_table(["Country", "Postings"], _value_counts(postings, "country")),
        "",
        _markdown_table(["Role family", "Postings"], _value_counts(postings, "role_family")),
    ]

    top_skill_rows = [
        [
            str(row["skill"]),
            str(int(row["count"])),
            f"{row['share']:.1%}",
            f"{row['ci_low']:.1%}–{row['ci_high']:.1%}",
        ]
        for _, row in counts.iterrows()
    ]
    report = [
        "# JobLens Report",
        "",
        *overview,
        "",
        "## Top skills",
        _markdown_table(["Skill", "Count", "Share", "95% Wilson interval"], top_skill_rows),
        "",
        f"![Top skills chart]({chart_path.name})",
        "",
        "## Group comparisons",
        *_format_comparisons(postings, "country", catalog_path),
        "",
        *_format_comparisons(postings, "role_family", catalog_path),
    ]

    if skills_path is not None or cv_path is not None:
        my_skills = load_my_skills(skills_path or cv_path, catalog, cv=cv_path is not None)
        match = match_postings(postings, my_skills, catalog)
        gap_rows = [
            [str(row["skill"]), f"{row['prevalence']:.1%}", f"{row['ci_low']:.1%}–{row['ci_high']:.1%}"]
            for _, row in match.gaps.head(10).iterrows()
        ]
        strength_rows = [
            [str(row["skill"]), f"{row['prevalence']:.1%}"]
            for _, row in match.strengths.head(10).iterrows()
        ]
        report.extend(
            [
                "",
                "## Your match",
                f"Mean coverage: **{match.mean_coverage:.1%}**",
                "",
                "### Top gaps",
                _markdown_table(["Skill", "Prevalence", "95% Wilson interval"], gap_rows),
                "",
                "### Top strengths",
                _markdown_table(["Skill", "Prevalence"], strength_rows),
            ]
        )

    report.extend(
        [
            "",
            "## Limitations",
            "- Keyword matching cannot tell required skills from nice-to-have skills.",
            "- Results depend on how postings were collected.",
            "- Small n gives wide intervals.",
            "- Many tests were run, hence Benjamini-Hochberg correction.",
            "",
            "## Reproduce",
            "```bash",
            "uv run joblens report "
            + _relative(folder)
            + (f" --skills {_relative(skills_path)}" if skills_path is not None else "")
            + (f" --cv {_relative(cv_path)}" if cv_path is not None else "")
            + f" --out {_relative(output)}",
            "```",
        ]
    )
    return "\n".join(report) + "\n"
