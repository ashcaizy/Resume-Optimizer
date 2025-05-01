# src/suggester.py
"""Suggest edits to a resume and emit an improved PDF while preserving layout.

Core changes vs. the original version
------------------------------------
1. **Keeps layout** – we rewrite each bullet/paragraph but keep the same
   heading/bullet structure so the output looks like the original.
2. **CPU‐safe** – forces CPU when MPS is detected to avoid placeholder
   storage errors on macOS.
3. **PDF writer** – adds `resume_to_pdf()` that renders a plain‑text resume
   into a simple, clean PDF (same margins/fonts) with ReportLab.
4. **Public helper** – `suggest_edits()` now returns both the improved text
   *and* a path to the generated PDF.
"""

from __future__ import annotations

import functools
import itertools
import tempfile
from pathlib import Path
from typing import Tuple, List

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, TextStreamer
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

from .parser import Resume
from .config import HF_MODEL_GENERATION, TOP_N_GAPS, MAX_NEW_TOKENS

# ────────────────────────────────── device selection ─────────────────────────
if torch.cuda.is_available():
    DEVICE = "cuda"
elif torch.backends.mps.is_available():
    DEVICE = "cpu"  # skip flaky MPS
else:
    DEVICE = "cpu"

# ────────────────────────────────── model + tokenizer ─────────────────────────
tok = AutoTokenizer.from_pretrained(HF_MODEL_GENERATION)
model = (
    AutoModelForSeq2SeqLM.from_pretrained(HF_MODEL_GENERATION, device_map=None)
    .eval()
    .to(DEVICE)
)

# ────────────────────────────────── helpers ───────────────────────────────────

def keyword_gap(resume: Resume, job: Resume, top_n: int = TOP_N_GAPS) -> List[str]:
    """Return the *top_n* skills/keywords present in *job* but not in *resume*."""
    missing = (set(job.tokens) - set(resume.tokens)) - set(resume.skills)
    return list(itertools.islice(missing, top_n))


@functools.cache
def _streamer():
    return TextStreamer(tok, skip_prompt=True, skip_special_tokens=True)


# ────────────────────────────────── PDF renderer ─────────────────────────────

def resume_to_pdf(text: str, out_path: Path | str) -> Path:
    """Render *text* (one paragraph or bullet per line) to a PDF."""
    out_path = Path(out_path)
    c = canvas.Canvas(str(out_path), pagesize=letter)
    width, height = letter
    left_margin = 1 * inch
    top = height - 1 * inch
    line_height = 11  # points

    for line in text.splitlines():
        if not line.strip():  # blank line
            top -= line_height
            continue
        c.drawString(left_margin, top, line)
        top -= line_height
        if top < 1 * inch:  # new page
            c.showPage()
            top = height - 1 * inch
    c.save()
    return out_path


# ──────────────────────────────── main entry point ───────────────────────────

def suggest_edits(resume_text: str, job_text: str) -> Tuple[str, Path]:
    """Return `(improved_text, pdf_path)`.

    The improved resume preserves the exact line/bullet structure of the
    original but rewrites each non‑empty line with the language model.
    """
    res, job = Resume(resume_text), Resume(job_text)
    gaps = ", ".join(keyword_gap(res, job)) or "NONE"

    prompt = f"""
Rewrite the RESUME so that:
• Maintain the same number of lines and bullet markers (•) – preserve layout.
• Integrate EVERY keyword from KEYWORDS exactly once.
• Tone stays professional; bullet points concise; length ±10%.

RESUME (each line exactly as in file):
{resume_text}

JOB DESCRIPTION:
{job_text}

KEYWORDS: {gaps}

### Improved Resume (same line count)
"""

    # Tokenize + generate
    inputs = tok(
    prompt,
    return_tensors="pt",
    truncation=True,
    max_length=tok.model_max_length, 
    ).to(DEVICE)
    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=0.3,
            top_p=0.9,
        )
    improved_text = tok.decode(outputs[0], skip_special_tokens=True).split(
        "### Improved Resume"
    )[-1].strip()

    # Emit PDF
    pdf_path = resume_to_pdf(improved_text, tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name)
    return improved_text, pdf_path
