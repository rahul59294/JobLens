# JobLens

Local-first CLI for understanding which skills appear in a folder of job descriptions.

## Quick start

```bash
uv sync
uv run pytest
uv run joblens ingest samples/jobs
uv run joblens skills samples/jobs
```

Each `.md` or `.txt` file may start with YAML front matter containing `title`,
`company`, `country`, `role_family`, `salary_min`, `salary_max`, and `currency`.
