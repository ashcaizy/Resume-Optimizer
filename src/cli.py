import typer
import rich
from pathlib import Path
from fpdf import FPDF
import unicodedata

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
    res_text = read_file(resume)
    if job_url:
        job_text = fetch_job(job_url)
    elif job:
        job_text = read_file(job)
    else:
        typer.echo("Provide --job or --job-url")
        raise typer.Exit(1)

    tf, sb = DualSimilarity(HF_MODEL_EMBED).score(res_text, job_text)
    rich.print(f"[bold]TF-IDF:[/] {tf:.3f}")
    rich.print(f"[bold]SBERT :[/] {sb:.3f}")

@app.command()
def suggest(
    resume: Path,
    job: Path = typer.Option(None),
    job_url: str = typer.Option(None),
    out: Path = typer.Option(None),
):
    res_text = read_file(resume)
    if job_url:
        job_text = fetch_job(job_url)
    elif job:
        job_text = read_file(job)
    else:
        typer.echo("Provide --job or --job-url")
        raise typer.Exit(1)

    # get the improved resume text (with line breaks preserved)
    improved = suggest_edits(res_text, job_text)

    # decide output PDF path
    pdf_out = out or resume.with_name(resume.stem + "_improved.pdf")

    # generate a simple PDF with the new content
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=12)

    for line in improved.split("\n"):
      # 1) normalize and drop any non-ASCII characters (e.g. en-dash, smart quotes)
        safe = unicodedata.normalize("NFKD", line)
        safe = safe.encode("ascii", "ignore").decode("ascii")
        pdf.multi_cell(0, 8, safe)

    pdf.output(str(pdf_out))

    rich.print(f"[green]Wrote://[/] {pdf_out}")

if __name__ == "__main__":
    app()
