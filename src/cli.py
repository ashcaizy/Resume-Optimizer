import typer, rich
from pathlib import Path
from .data_loader import read_file
from .similarity  import DualSimilarity
from .suggester   import suggest_resume
from .job_scraper  import fetch as fetch_job
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

app = typer.Typer(help="Resume Optimizer CLI")
# Load the trained model and tokenizer
model_path = "models/resume-fit"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

@app.command()
def analyze(
    resume: Path,
    job: Path     = typer.Option(None, help="Path to job description file"),
    job_url: str  = typer.Option(None, help="URL of online job posting"),
):
    """Show similarity scores and compatibility prediction between RESUME and JOB."""
    res_text = read_file(resume)
    job_text = fetch_job(job_url) if job_url else read_file(job) if job else None
    if job_text is None:
        typer.echo("Provide --job or --job-url", err=True)
        raise typer.Exit(1)

    # Calculate similarity scores
    tf, sb = DualSimilarity(hf_model="sentence-transformers/all-MiniLM-L6-v2").score(res_text, job_text)
    rich.print(f"[bold]TF‑IDF:[/] {tf:.3f}")
    rich.print(f"[bold]SBERT :[/] {sb:.3f}")

    # Predict compatibility using the trained model
    inputs = tokenizer(
        res_text,
        job_text,
        truncation=True,
        padding="max_length",
        max_length=512,
        return_tensors="pt",
    )
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        predicted_class = torch.argmax(logits, dim=1).item()

    rich.print(f"[bold green]Predicted Compatibility Class:[/] {predicted_class}")

def _safe_break_line(line: str, max_len: int = 40) -> str:
    """
    Split any token longer than max_len into real spaces
    so FPDF can wrap it without error.
    """
    pieces = []
    for token in line.split():
        if len(token) > max_len:
            for i in range(0, len(token), max_len):
                pieces.append(token[i : i + max_len])
        else:
            pieces.append(token)
    return " ".join(pieces)

@app.command()
def suggest(
    resume: Path,
    job: Path     = typer.Option(None, help="Path to job description file"),
    job_url: str  = typer.Option(None, help="URL of online job posting"),
    out: Path     = typer.Option(None, help="Output path (.pdf or .md)"),
    markdown: bool = typer.Option(False, "--md", help="Save result as Markdown"),
):
    """Generate résumé improvements plus keyword recommendations."""
    res_text = read_file(resume)
    job_text = fetch_job(job_url) if job_url else read_file(job) if job else None
    if job_text is None:
        typer.echo("Provide --job or --job-url", err=True)
        raise typer.Exit(1)

    rich.print("[yellow]🔍 Analyzing…[/]")
    improved, gaps = suggest_resume(res_text, job_text)

    # Build Markdown document (with emojis)
    kw_md = "## 🔑 Keywords / Skills to Consider Adding\n\n" + "\n".join(f"- {k}" for k in gaps)
    md_doc = f"{kw_md}\n\n---\n\n## 📄 Revised Resume\n\n{improved}"

    default = resume.with_name(resume.stem + ("_improved.md" if markdown else "_improved.pdf"))
    out_path = out or default

    # ── Markdown output ────────────────────────────────
    if markdown or out_path.suffix.lower() == ".md":
        out_path.write_text(md_doc, encoding="utf-8")
        rich.print(f"[green]Wrote →[/] {out_path}")
        return

    # ── PDF output ────────────────────────────────────
    # strip emojis (they break Helvetica), but leave text/structure intact
    pdf_text = md_doc.replace("🔑", "").replace("📄", "")

    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(True, margin=15)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    # Compute a positive cell width: full page width minus both margins
    usable_w = pdf.w - pdf.l_margin - pdf.r_margin

    for line in pdf_text.splitlines():
        safe_line = _safe_break_line(line)
        # pass usable_w instead of 0
        pdf.multi_cell(usable_w, 6, safe_line)

    pdf.output(str(out_path))
    rich.print(f"[green]Wrote →[/] {out_path}")

if __name__ == "__main__":
    app()
