# JobLens

[![CI](https://github.com/rahul59294/JobLens/actions/workflows/ci.yml/badge.svg)](https://github.com/rahul59294/JobLens/actions/workflows/ci.yml)

JobLens is a local-first CLI for analyzing job descriptions. It shows which
skills employers request, how prevalence differs by country or role, and how
well a skills list or CV matches the postings. It is designed for private,
reproducible analysis: postings and personal files stay on your machine, with
no network calls or API keys.

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Input format

Use one `.md` or `.txt` file per posting. A file may begin with optional YAML
front matter, followed by free-text job description content:

```yaml
---
title: Data Analyst
company: Example Co
country: Australia
role_family: data analyst
salary_min: 80000
salary_max: 100000
currency: AUD
---
```

Supported front matter fields are `title`, `company`, `country`, `role_family`,
`salary_min`, `salary_max`, and `currency`.

## Commands

Ingest postings into a normalized CSV:

```bash
uv run joblens ingest samples/jobs
```

Show skill counts, shares, and 95% Wilson intervals:

```bash
uv run joblens skills samples/jobs
```

Compare countries or role families using Fisher/chi-square tests and
Benjamini-Hochberg adjusted p-values:

```bash
uv run joblens compare samples/jobs --by country
uv run joblens compare samples/jobs --by role_family
```

Match a one-skill-per-line file or a free-text CV:

```bash
uv run joblens match samples/jobs --skills samples/my_skills.example.txt
uv run joblens match samples/jobs --cv cv.txt
```

Generate a Markdown report and chart:

```bash
uv run joblens report samples/jobs \
  --skills samples/my_skills.example.txt \
  --out reports/report.md
```

See the generated example report at
[samples/report_demo.md](samples/report_demo.md).

## Use your own postings

Put private postings in `data/private/` and point commands at that directory:

```bash
uv run joblens report data/private --skills my_skills.txt --out reports/private.md
```

The `data/private/` directory is ignored by Git. Never commit real postings,
CVs, skills files, credentials, or other personal data.

## Limitations

- Keyword matching cannot distinguish required skills from nice-to-have skills.
- Results depend on how postings were collected and represented.
- Small samples produce wide confidence intervals and unstable comparisons.
- Many statistical tests are run, so Benjamini-Hochberg correction is applied.
- Skill aliases and wording not present in the catalog will not be recognized.

## Docker

Build and run the default sample report:

```bash
docker build -t joblens .
docker run --rm joblens
```

The image uses Python 3.12, uv, and the non-interactive matplotlib `Agg`
backend. The default command writes `reports/report.md` and its chart inside
the container. To retain output locally, mount a directory:

```bash
mkdir -p reports
docker run --rm -v "$PWD/reports:/app/reports" joblens
```

## Tests

```bash
uv run pytest
```

## Built with OmniRush

Sessions: _placeholder_
