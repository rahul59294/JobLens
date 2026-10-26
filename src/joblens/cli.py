"""Command-line interface for JobLens."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .ingest import ingest, load_postings
from .skills import load_catalog, skill_counts

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
    table = Table("skill", "count", "share")
    for _, row in counts.iterrows():
        table.add_row(str(row["skill"]), str(int(row["count"])), f"{row['share']:.1%}")
    console.print(table)


if __name__ == "__main__":
    app()
