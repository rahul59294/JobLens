FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

ENV MPLBACKEND=Agg
ENV MPLCONFIGDIR=/tmp/mpl

CMD ["uv", "run", "joblens", "report", "samples/jobs", "--skills", "samples/my_skills.example.txt", "--out", "reports/report.md"]
