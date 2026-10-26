import pandas as pd

from joblens.skills import extract_skills


def test_word_boundaries_keep_short_and_punctuation_heavy_skills_exact() -> None:
    catalog = pd.DataFrame(
        [
            {"skill": "R", "category": "languages", "aliases": ""},
            {"skill": "SQL", "category": "languages", "aliases": ""},
            {"skill": "C++", "category": "languages", "aliases": "CPP"},
            {"skill": "Power BI", "category": "BI tools", "aliases": "PowerBI"},
            {"skill": "scikit-learn", "category": "stats/ML", "aliases": "sklearn"},
        ]
    )

    text = "R and SQL are useful. C++ and Power BI are required; scikit-learn is a bonus."
    assert extract_skills(text, catalog) == ["R", "SQL", "C++", "Power BI", "scikit-learn"]


def test_word_boundaries_do_not_match_inside_larger_words() -> None:
    catalog = pd.DataFrame(
        [
            {"skill": "R", "category": "languages", "aliases": ""},
            {"skill": "SQL", "category": "languages", "aliases": ""},
            {"skill": "C++", "category": "languages", "aliases": ""},
            {"skill": "Power BI", "category": "BI tools", "aliases": ""},
        ]
    )

    text = "Research SQLAlchemy C++17 and Power BI2 are not exact skill mentions."
    assert extract_skills(text, catalog) == []


def test_single_letter_r_does_not_match_ampersand_names() -> None:
    catalog = pd.DataFrame([{"skill": "R", "category": "languages", "aliases": ""}])

    for text in ("R&D", "Q&A", "R&R"):
        assert extract_skills(text, catalog) == []


def test_single_letter_r_matches_common_separators() -> None:
    catalog = pd.DataFrame([{"skill": "R", "category": "languages", "aliases": ""}])

    for text in ("R", "R/Python", "R, SQL", "(R)"):
        assert extract_skills(text, catalog) == ["R"]
