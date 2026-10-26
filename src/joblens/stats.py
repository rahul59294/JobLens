"""Statistical summaries and group comparisons for job postings."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Return the Wilson score interval for *k* successes out of *n* trials."""

    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= k <= n:
        raise ValueError("k must be between 0 and n")
    p = k / n
    denominator = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
    return centre - margin, centre + margin


COMPARISON_COLUMNS = [
    "skill",
    "group",
    "group_n",
    "other_n",
    "odds_ratio",
    "p_value",
    "p_adjusted",
    "method",
    "small_sample",
]


def _as_skill_set(value: Any) -> set[str]:
    if isinstance(value, str):
        return {part.strip() for part in re.split(r"\s*\|\s*", value) if part.strip()}
    if isinstance(value, Iterable) and not isinstance(value, (bytes, str)):
        return {str(skill) for skill in value}
    if value is None or pd.isna(value):
        return set()
    return {str(value)}


def _mention_matrix(df: pd.DataFrame, catalog: str | Path) -> pd.DataFrame:
    if "skills" in df.columns:
        mentions = [_as_skill_set(value) for value in df["skills"]]
    elif "text" in df.columns:
        from .skills import extract_skills, load_catalog

        skill_catalog = load_catalog(catalog)
        mentions = [set(extract_skills(str(text), skill_catalog)) for text in df["text"].fillna("")]
    else:
        raise ValueError("compare requires a 'text' or 'skills' column")

    all_skills = sorted({skill for row in mentions for skill in row})
    return pd.DataFrame(
        [{skill: skill in row for skill in all_skills} for row in mentions],
        index=df.index,
        columns=all_skills,
    )


def _benjamini_hochberg(p_values: list[float]) -> list[float]:
    total = len(p_values)
    adjusted = [0.0] * total
    running = 1.0
    ordered = sorted(range(total), key=p_values.__getitem__)
    for rank, index in reversed(list(enumerate(ordered, start=1))):
        running = min(running, p_values[index] * total / rank)
        adjusted[index] = min(running, 1.0)
    return adjusted


def compare(df: pd.DataFrame, by: str, catalog: str | Path = "data/skills.csv") -> pd.DataFrame:
    """Compare skill prevalence in each group against all other postings.

    Fisher's exact test is used unless every expected cell count is at least five,
    in which case an uncorrected chi-square test is used. BH correction spans all
    skill/group tests returned by this function.
    """

    if by not in df.columns:
        raise ValueError(f"Grouping column not found: {by}")
    if df.empty:
        return pd.DataFrame(columns=COMPARISON_COLUMNS)

    valid = df[df[by].notna()].copy()
    mentions = _mention_matrix(valid, catalog)
    skill_counts = mentions.sum(axis=0)
    skills = [skill for skill, count in skill_counts.items() if count >= 2]
    group_sizes = valid[by].value_counts()
    small_sample = bool((group_sizes < 5).any())
    rows: list[dict[str, Any]] = []

    for skill in skills:
        has_skill = mentions[skill]
        for group, group_n in group_sizes.items():
            in_group = valid[by] == group
            other = ~in_group
            other_n = int(other.sum())
            if other_n == 0:
                continue
            a = int((in_group & has_skill).sum())
            b = int((in_group & ~has_skill).sum())
            c = int((other & has_skill).sum())
            d = int((other & ~has_skill).sum())
            table = [[a, b], [c, d]]
            expected = chi2_contingency(table, correction=False)[3]
            if (expected >= 5).all():
                p_value = float(chi2_contingency(table, correction=False)[1])
                method = "chi-square"
            else:
                p_value = float(fisher_exact(table)[1])
                method = "Fisher exact"

            cells = [a, b, c, d]
            if 0 in cells:
                odds_ratio = ((a + 0.5) * (d + 0.5)) / ((b + 0.5) * (c + 0.5))
            else:
                odds_ratio = (a * d) / (b * c)
            rows.append(
                {
                    "skill": skill,
                    "group": group,
                    "group_n": int(group_n),
                    "other_n": other_n,
                    "odds_ratio": float(odds_ratio),
                    "p_value": p_value,
                    "method": method,
                    "small_sample": small_sample,
                }
            )

    if not rows:
        return pd.DataFrame(columns=COMPARISON_COLUMNS)
    result = pd.DataFrame(rows)
    result["p_adjusted"] = _benjamini_hochberg(result["p_value"].tolist())
    return result.sort_values(["p_adjusted", "p_value", "skill", "group"], ignore_index=True)[
        COMPARISON_COLUMNS
    ]
