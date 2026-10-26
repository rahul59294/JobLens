# JobLens

Local-first CLI that analyzes a folder of job descriptions: which skills employers
ask for, how often, how that differs by role/country, and how well your CV and
skill list match.

## Stack
- Python 3.12 (.python-version), uv (uv.lock committed)
- pandas, typer, rich, matplotlib, pyyaml, pytest. No network calls, no API keys.

## Layout
src/joblens/{ingest.py, skills.py, stats.py, match.py, report.py, cli.py}
data/skills.csv (skill, category, aliases separated by |), committed
samples/jobs/ (10 synthetic job descriptions, committed)
data/private/ (real postings, gitignored)
tests/

## Input format
One .md/.txt file per job. Optional front matter: title, company, country,
role_family, salary_min, salary_max, currency. Body is free text.

## Commands
- `uv run joblens ingest <folder>` -> data/jobs.csv
- `uv run joblens skills <folder>` -> skill frequency table
- `uv run joblens report <folder> --skills my_skills.txt --cv cv.txt --out report.md`
- Test: `uv run pytest`

## Rules
- Skill matching: case-insensitive, word-boundary regex on skill + aliases.
  "R" and "SQL" must not match inside other words; handle "Power BI", "C++", "scikit-learn".
- Prevalence = share of postings mentioning a skill, with 95% Wilson interval.
- Country/role comparisons: Fisher exact (chi-square if all expected counts >= 5),
  report effect size, flag small samples.
- Relative paths only. Never commit real personal data.
- Short readable code. Update README when behavior changes.
