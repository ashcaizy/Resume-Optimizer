import typer
import rich
import shutil
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

    # generate improved text and a temporary PDF path
    improved_text, tmp_pdf = suggest_edits(res, job_txt)

    # write out the improved markdown
    md_out = out or resume.with_name(resume.stem + "_improved.md")
    md_out.write_text(improved_text, encoding="utf-8")
    rich.print(f"[green]Wrote MD://[/] {md_out}")

    # move the PDF into the same folder as the resume
    pdf_out = resume.with_name(resume.stem + "_improved.pdf")
    shutil.move(str(tmp_pdf), str(pdf_out))
    rich.print(f"[green]Wrote PDF://[/] {pdf_out}")

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

    # for debugging; prints the raw tuple
    print(suggest_edits(res, job_txt))

if __name__ == "__main__":
    app()
