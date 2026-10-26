from pathlib import Path

from joblens.ingest import load_postings, parse_document


def test_parse_front_matter(tmp_path: Path) -> None:
    posting = tmp_path / "analyst.md"
    posting.write_text(
        "---\n"
        "title: Data Analyst\n"
        "company: Example Co\n"
        "country: Australia\n"
        "role_family: data analyst\n"
        "salary_min: 80000\n"
        "salary_max: 100000\n"
        "currency: AUD\n"
        "---\n\nUse SQL and Python.\n",
        encoding="utf-8",
    )

    record = parse_document(posting)
    assert record["title"] == "Data Analyst"
    assert record["company"] == "Example Co"
    assert record["salary_min"] == 80000
    assert record["text"] == "Use SQL and Python."


def test_missing_front_matter_uses_filename_and_body(tmp_path: Path) -> None:
    posting = tmp_path / "plain_posting.txt"
    posting.write_text("A plain posting with no metadata.\n", encoding="utf-8")

    postings = load_postings(tmp_path)
    assert len(postings) == 1
    assert postings.loc[0, "title"] == "plain_posting"
    assert postings.loc[0, "company"] is None
    assert postings.loc[0, "text"] == "A plain posting with no metadata."
