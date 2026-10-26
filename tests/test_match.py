from pathlib import Path

import pandas as pd

from joblens.match import load_my_skills, match_postings


def _catalog() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"skill": "Python", "category": "languages", "aliases": "py"},
            {"skill": "SQL", "category": "languages", "aliases": ""},
            {"skill": "R", "category": "languages", "aliases": ""},
            {"skill": "Power BI", "category": "BI tools", "aliases": "PowerBI"},
        ]
    )


def _postings() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "title": ["One", "Two", "Three"],
            "company": ["A", "B", "C"],
            "country": ["AU", "IN", "UK"],
            "text": ["Python and SQL", "SQL and R", "Power BI"],
        }
    )


def test_skills_file_parsing_and_cv_text_extraction(tmp_path: Path) -> None:
    skills_file = tmp_path / "skills.txt"
    skills_file.write_text("Python\nPowerBI\n", encoding="utf-8")
    cv_file = tmp_path / "cv.txt"
    cv_file.write_text("Experienced with SQL and Power BI.", encoding="utf-8")

    catalog = _catalog()
    assert load_my_skills(skills_file, catalog) == {"Python", "Power BI"}
    assert load_my_skills(cv_file, catalog, cv=True) == {"SQL", "Power BI"}


def test_match_coverage_gaps_and_strengths() -> None:
    result = match_postings(_postings(), {"Python", "SQL"}, _catalog())

    assert result.mean_coverage == 0.5
    assert result.coverage["coverage"].tolist() == [1.0, 0.5, 0.0]
    assert result.gaps["skill"].tolist() == ["Power BI", "R"]
    assert result.gaps["prevalence"].tolist() == [1 / 3, 1 / 3]
    assert result.strengths["skill"].tolist() == ["SQL", "Python"]
    assert result.strengths["prevalence"].tolist() == [2 / 3, 1 / 3]


def test_empty_skills_file_has_zero_coverage(tmp_path: Path) -> None:
    skills_file = tmp_path / "empty.txt"
    skills_file.write_text("\n", encoding="utf-8")

    result = match_postings(_postings(), load_my_skills(skills_file, _catalog()), _catalog())
    assert result.my_skills == set()
    assert result.mean_coverage == 0.0
    assert result.coverage["coverage"].tolist() == [0.0, 0.0, 0.0]
