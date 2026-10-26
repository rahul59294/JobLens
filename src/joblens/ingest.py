"""Read job description files into a normalized pandas DataFrame."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

FRONT_MATTER_FIELDS = (
    "title",
    "company",
    "country",
    "role_family",
    "salary_min",
    "salary_max",
    "currency",
)


def parse_document(path: Path) -> dict[str, Any]:
    """Parse one Markdown or text posting, including optional YAML front matter."""

    raw = path.read_text(encoding="utf-8")
    metadata: dict[str, Any] = {}
    body = raw

    lines = raw.splitlines(keepends=True)
    if lines and lines[0].lstrip("\ufeff").strip() == "---":
        end = next((index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"), None)
        if end is not None:
            front_matter = "".join(lines[1:end])
            parsed = yaml.safe_load(front_matter) or {}
            if not isinstance(parsed, dict):
                raise ValueError(f"Front matter in {path} must be a YAML mapping")
            metadata = {key: parsed.get(key) for key in FRONT_MATTER_FIELDS if key in parsed}
            body = "".join(lines[end + 1 :])

    record: dict[str, Any] = {
        "path": str(path),
        "filename": path.name,
        "title": metadata.get("title") or path.stem,
        "company": metadata.get("company"),
        "country": metadata.get("country"),
        "role_family": metadata.get("role_family"),
        "salary_min": metadata.get("salary_min"),
        "salary_max": metadata.get("salary_max"),
        "currency": metadata.get("currency"),
        "text": body.strip(),
    }
    return record


def load_postings(folder: str | Path) -> pd.DataFrame:
    """Read all `.md` and `.txt` files in *folder* into a DataFrame."""

    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise NotADirectoryError(f"Posting folder does not exist: {folder_path}")

    paths = sorted(
        path for path in folder_path.iterdir() if path.is_file() and path.suffix.lower() in {".md", ".txt"}
    )
    columns = ["path", "filename", *FRONT_MATTER_FIELDS, "text"]
    return pd.DataFrame([parse_document(path) for path in paths], columns=pd.Index(columns))


def ingest(folder: str | Path, output: str | Path = "data/jobs.csv") -> pd.DataFrame:
    """Load postings and write the normalized records to a CSV file."""

    postings = load_postings(folder)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    postings.to_csv(output_path, index=False)
    return postings
