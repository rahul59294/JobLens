"""Match a person's skills against a collection of job postings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .skills import extract_skills
from .stats import wilson_interval


@dataclass
class MatchResult:
    """Coverage, gaps, and strengths for one person's skill set."""

    my_skills: set[str]
    mean_coverage: float
    coverage: pd.DataFrame
    gaps: pd.DataFrame
    strengths: pd.DataFrame


def extract_my_skills(text: str, catalog: pd.DataFrame) -> set[str]:
    """Extract canonical catalog skills from free text such as a CV."""

    return set(extract_skills(text, catalog))


def load_my_skills(
    path: str | Path,
    catalog: pd.DataFrame,
    *,
    cv: bool = False,
) -> set[str]:
    """Load a skill set from a one-skill-per-line file or from CV text."""

    text = Path(path).read_text(encoding="utf-8")
    if cv:
        return extract_my_skills(text, catalog)

    skills: set[str] = set()
    for line in text.splitlines():
        if line.strip():
            skills.update(extract_my_skills(line, catalog))
    return skills


def _posting_skill_sets(postings: pd.DataFrame, catalog: pd.DataFrame) -> list[set[str]]:
    return [
        set(extract_skills(str(text), catalog))
        for text in postings["text"].fillna("")
    ]


def coverage_by_posting(
    postings: pd.DataFrame,
    my_skills: set[str],
    catalog: pd.DataFrame,
) -> pd.DataFrame:
    """Return each posting's share of requested skills covered by the user."""

    rows = []
    for (_, posting), posting_skills in zip(postings.iterrows(), _posting_skill_sets(postings, catalog)):
        rows.append(
            {
                "title": posting.get("title"),
                "company": posting.get("company"),
                "country": posting.get("country"),
                "coverage": (
                    len(posting_skills & my_skills) / len(posting_skills)
                    if posting_skills
                    else 0.0
                ),
            }
        )
    return pd.DataFrame(rows, columns=pd.Index(["title", "company", "country", "coverage"])).sort_values(
        "coverage", ascending=False, ignore_index=True
    )


def _prevalence_table(
    posting_skill_sets: list[set[str]],
    my_skills: set[str],
    *,
    have: bool,
) -> pd.DataFrame:
    total = len(posting_skill_sets)
    counts: dict[str, int] = {}
    for posting_skills in posting_skill_sets:
        for skill in posting_skills:
            counts[skill] = counts.get(skill, 0) + 1

    rows = []
    for skill, count in counts.items():
        if (skill in my_skills) != have:
            continue
        prevalence = count / total if total else 0.0
        low, high = wilson_interval(count, total) if total else (0.0, 0.0)
        rows.append(
            {
                "skill": skill,
                "count": count,
                "prevalence": prevalence,
                "ci_low": low,
                "ci_high": high,
            }
        )
    return pd.DataFrame(
        rows,
        columns=pd.Index(["skill", "count", "prevalence", "ci_low", "ci_high"]),
    ).sort_values(["prevalence", "skill"], ascending=[False, True], ignore_index=True)


def match_postings(
    postings: pd.DataFrame,
    my_skills: set[str],
    catalog: pd.DataFrame,
) -> MatchResult:
    """Calculate coverage, missing skills, and owned skills used by postings."""

    posting_skill_sets = _posting_skill_sets(postings, catalog)
    coverage = coverage_by_posting(postings, my_skills, catalog)
    mean_coverage = float(coverage["coverage"].mean()) if not coverage.empty else 0.0
    return MatchResult(
        my_skills=my_skills,
        mean_coverage=mean_coverage,
        coverage=coverage,
        gaps=_prevalence_table(posting_skill_sets, my_skills, have=False),
        strengths=_prevalence_table(posting_skill_sets, my_skills, have=True),
    )
