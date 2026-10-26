"""Skill catalog loading and safe, case-insensitive skill extraction."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

TOKEN_CHARS = r"A-Za-z0-9_+#"


def load_catalog(path: str | Path = "data/skills.csv") -> pd.DataFrame:
    """Load the committed skill catalog."""

    catalog = pd.read_csv(path, keep_default_na=False)
    required = {"skill", "category", "aliases"}
    missing = required.difference(catalog.columns)
    if missing:
        raise ValueError(f"Skill catalog is missing columns: {', '.join(sorted(missing))}")
    return catalog


def _skill_pattern(term: str) -> re.Pattern[str]:
    """Build a boundary pattern that also handles punctuation-heavy names."""

    escaped = re.escape(term.strip())
    return re.compile(rf"(?<![{TOKEN_CHARS}]){escaped}(?![{TOKEN_CHARS}])", re.IGNORECASE)


def extract_skills(text: str, catalog: pd.DataFrame) -> list[str]:
    """Return catalog skill names mentioned in *text*, once each.

    Boundaries prevent short names such as ``R`` and ``SQL`` from matching inside
    larger words, while allowing names such as ``C++``, ``Power BI``, and
    ``scikit-learn`` to match exactly.
    """

    found: list[str] = []
    for _, row in catalog.iterrows():
        terms = [str(row["skill"])]
        if str(row["aliases"]).strip():
            terms.extend(alias.strip() for alias in str(row["aliases"]).split("|") if alias.strip())
        if any(_skill_pattern(term).search(text) for term in terms):
            found.append(str(row["skill"]))
    return found


def skill_counts(postings: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    """Count postings mentioning each catalog skill and calculate its share."""

    counts = {str(skill): 0 for skill in catalog["skill"]}
    for text in postings["text"].fillna(""):
        for skill in extract_skills(str(text), catalog):
            counts[skill] += 1

    total = len(postings)
    rows = [
        {"skill": skill, "count": count, "share": count / total if total else 0.0}
        for skill, count in counts.items()
        if count
    ]
    return pd.DataFrame(rows, columns=pd.Index(["skill", "count", "share"])).sort_values(
        ["count", "skill"], ascending=[False, True], ignore_index=True
    )
