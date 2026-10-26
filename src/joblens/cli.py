"""Command-line interface for JobLens."""

from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from .ingest import ingest, load_postings
from .match import load_my_skills, match_postings
from .skills import load_catalog, skill_counts
from .stats import compare

app = typer.Typer(help="Analyze skills in local job descriptions.")
console = Console()


@app.command("ingest")
def ingest_command(
    folder: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    output: Path = typer.Option(Path("data/jobs.csv"), "--output", "-o"),
) -> None:
    """Read job files and write normalized records to CSV."""

    postings = ingest(folder, output)
    console.print(f"Ingested [bold]{len(postings)}[/bold] postings to {output}")


@app.command("skills")
def skills_command(
    folder: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    catalog: Path = typer.Option(Path("data/skills.csv"), "--catalog"),
) -> None:
    """Show skill frequency across postings."""

    postings = load_postings(folder)
    counts = skill_counts(postings, load_catalog(catalog))
    console.print(f"n postings: {len(postings)}")
    table = Table("skill", "count", "share", "95% low", "95% high")
    for _, row in counts.iterrows():
        table.add_row(
            str(row["skill"]),
            str(int(row["count"])),
            f"{row['share']:.1%}",
            f"{row['ci_low']:.1%}",
            f"{row['ci_high']:.1%}",
        )
    console.print(table)


@app.command("compare")
def compare_command(
    folder: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    by: str = typer.Option(..., "--by", help="Grouping field: country or role_family"),
    catalog: Path = typer.Option(Path("data/skills.csv"), "--catalog"),
) -> None:
    """Compare skill prevalence by country or role family."""

    if by not in {"country", "role_family"}:
        raise typer.BadParameter("must be country or role_family", param_hint="--by")
    results = compare(load_postings(folder), by, catalog)
    if results.empty:
        console.print("No skills were mentioned in at least 2 postings.")
        return
    if results["small_sample"].any():
        console.print("[yellow]Warning: one or more groups contain fewer than 5 postings.[/yellow]")
    table = Table("skill", "group", "odds ratio", "p-value", "BH p-value", "method")
    for _, row in results.iterrows():
        table.add_row(
            str(row["skill"]),
            str(row["group"]),
            f"{row['odds_ratio']:.2f}",
            f"{row['p_value']:.4f}",
            f"{row['p_adjusted']:.4f}",
            str(row["method"]),
        )
    console.print(table)


@app.command("match")
def match_command(
    folder: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    skills: Path | None = typer.Option(None, "--skills", help="Text file with one skill per line"),
    cv: Path | None = typer.Option(None, "--cv", help="Free-text CV file"),
    catalog: Path = typer.Option(Path("data/skills.csv"), "--catalog"),
) -> None:
    """Match a skill list or CV against job postings."""

    if (skills is None) == (cv is None):
        raise typer.BadParameter("provide exactly one of --skills or --cv")
    skill_catalog = load_catalog(catalog)
    my_skills = load_my_skills(skills or cv, skill_catalog, cv=cv is not None)
    result = match_postings(load_postings(folder), my_skills, skill_catalog)

    console.print(f"Mean coverage: [bold]{result.mean_coverage:.1%}[/bold]")
    _print_match_table("Top 10 gaps", result.gaps.head(10), include_count=True)
    _print_match_table("Top 10 strengths", result.strengths.head(10), include_count=False)

    console.print("Per-posting coverage")
    table = Table("title", "company", "country", "coverage")
    for _, row in result.coverage.iterrows():
        table.add_row(
            str(row["title"] or ""),
            str(row["company"] or ""),
            str(row["country"] or ""),
            f"{row['coverage']:.1%}",
        )
    console.print(table)


def _print_match_table(title: str, rows: pd.DataFrame, *, include_count: bool) -> None:
    console.print(title)
    table = Table("skill", "count", "prevalence", "95% low", "95% high")
    for _, row in rows.iterrows():
        table.add_row(
            str(row["skill"]),
            str(int(row["count"])) if include_count else "",
            f"{row['prevalence']:.1%}",
            f"{row['ci_low']:.1%}",
            f"{row['ci_high']:.1%}",
        )
    console.print(table)


if __name__ == "__main__":
    app()
