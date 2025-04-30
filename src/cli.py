import typer, rich
from pathlib import Path
from .data_loader import read_file
from .similarity import DualSimilarity
from .suggester import suggest_edits
from .config import HF_MODEL_EMBED
from .job_scraper import fetch as fetch_job

app = typer.Typer()

@app.command()
def analyze(
    resume: Path,
    job: Path = typer.Option(None),
    job_url: str = typer.Option(None),
):
    res = read_file(resume)
    if job_url:
        job_txt = fetch_job(job_url)
    elif job:
        job_txt = read_file(job)
    else:
        typer.echo("Provide --job or --job-url")
        raise typer.Exit(1)
    tf, sb = DualSimilarity(HF_MODEL_EMBED).score(res, job_txt)
    rich.print(f"[bold]TF-IDF:[/] {tf:.3f}")
    rich.print(f"[bold]SBERT :[/] {sb:.3f}")

@app.command()
def suggest(
    resume: Path,
    job: Path = typer.Option(None),
    job_url: str = typer.Option(None),
    out: Path = typer.Option(None),
):
    res = read_file(resume)
    if job_url:
        job_txt = fetch_job(job_url)
    elif job:
        job_txt = read_file(job)
    else:
        typer.echo("Provide --job or --job-url")
        raise typer.Exit(1)

    improved = suggest_edits(res, job_txt)
    of = out or resume.with_name(resume.stem + "_improved.md")
    of.write_text(improved, encoding="utf-8")
    rich.print(f"[green]Wrote://[/] {of}")

@app.command()
def full_optimize(
    resume: Path,
    job: Path = typer.Option(None),
    job_url: str = typer.Option(None),
):
    res = read_file(resume)
    if job_url:
        job_txt = fetch_job(job_url)
    elif job:
        job_txt = read_file(job)
    else:
        typer.echo("Provide --job or --job-url")
        raise typer.Exit(1)
    print(suggest_edits(res, job_txt))

if __name__ == "__main__":
    app()
