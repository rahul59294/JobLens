# JobLens

Local-first CLI for understanding which skills appear in a folder of job descriptions.

## Quick start

```bash
uv sync
uv run pytest
uv run joblens ingest samples/jobs
uv run joblens skills samples/jobs
uv run joblens compare samples/jobs --by country
uv run joblens compare samples/jobs --by country
```

Each `.md` or `.txt` file may start with YAML front matter containing `title`,
`company`, `country`, `role_family`, `salary_min`, `salary_max`, and `currency`.

The skills command reports prevalence with a 95% Wilson interval. The compare
command uses Fisher's exact test for small expected counts and adjusts its
p-values across all skill/group tests with Benjamini-Hochberg correction.

The skills command reports prevalence with a 95% Wilson interval. The compare
command uses Fisher's exact test for small expected counts and adjusts its
p-values across all skill/group tests with Benjamini-Hochberg correction.
