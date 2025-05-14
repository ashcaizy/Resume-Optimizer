# src/suggester.py
"""
Smart résumé suggester.

Improvements over the previous version
--------------------------------------
1. **Gibberish filter**
   • Keeps only alphabetic words 3‑20 chars containing ≥ 1 vowel and
     *no* run of ≥ 4 consonants.

2. **Keyword use‑once policy**
   • Each missing keyword is suggested at most once, never on contact lines.

3. **Context‑aware action verbs**
   • If a bullet doesn’t start with a strong verb, pick a tailored action verb based
     on cues in the bullet.

4. **Clean markdown**
   • Single header section; each line printed once with bracketed suggestions.

Public API
----------
`suggest_resume(resume_text, job_text, top_n_keywords=TOP_N_GAPS)`
    → (markdown_str, missing_keywords)

`suggest_edits(resume_text, job_text)`
    Legacy shim returning only the markdown.
"""
from __future__ import annotations

import logging
import re
from collections import Counter
from typing import List, Tuple
from pathlib import Path

import spacy
from fpdf import FPDF
from .config import TOP_N_GAPS

# --------------------------------------------------------------------------- #
# spaCy setup
# --------------------------------------------------------------------------- #
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
nlp = spacy.load("en_core_web_sm", disable=["ner"])

# --------------------------------------------------------------------------- #
# Constants & regexes
# --------------------------------------------------------------------------- #
_WORD_RE = re.compile(r"^[A-Za-z]{3,20}$")
VOWELS = set("aeiouAEIOU")
CONSONANT_RUN_RE = re.compile(r"[bcdfghjklmnpqrstvwxyz]{4,}", flags=re.I)

BULLET_RE  = re.compile(r"^[\s]*[-o\*•▪]")
CONTACT_RE = re.compile(r"@|https?://|\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b")
DIGIT_RE   = re.compile(r"\d")

# Strong action verbs (lower‑case)
ACTION_VERBS = {
    "achieved","adapted","analyzed","built","captured","collaborated",
    "conceived","created","debugged","decreased","designed","developed",
    "directed","drove","engineered","enhanced","established","evaluated",
    "exceeded","executed","expanded","facilitated","forecasted","founded",
    "generated","grew","implemented","improved","increased","initiated",
    "launched","led","managed","negotiated","optimized","organized",
    "overhauled","oversaw","planned","produced","programmed","reduced",
    "refactored","researched","resolved","restructured","revamped",
    "saved","scaled","simplified","solved","streamlined","spearheaded",
    "strengthened","tested","trained","transformed","won",
}

# Mapping cues → verbs to pick tailored verbs
CUE_TO_VERB = {
    "analysis":"Analyzed","data":"Analyzed","design":"Designed",
    "develop":"Developed","research":"Researched","implement":"Implemented",
    "test":"Tested","manage":"Managed","lead":"Led","optim":"Optimized",
    "build":"Built","deploy":"Deployed","reduce":"Reduced","increase":"Increased",
    "sales":"Increased","revenue":"Increased","team":"Led","customer":"Improved",
    "python":"Programmed","battery":"Engineered","hydrogen":"Engineered",
}

# --------------------------------------------------------------------------- #
# Utility helpers
# --------------------------------------------------------------------------- #

def _looks_like_real_word(w: str) -> bool:
    """Filter out gibberish."""
    if not _WORD_RE.match(w):
        return False
    if not any(c in VOWELS for c in w):
        return False
    if CONSONANT_RUN_RE.search(w):
        return False
    return True


def _keyword_gaps(res: str, job: str, top: int) -> List[str]:
    """Extract up to top missing keywords (title‑cased)."""
    res_doc = nlp(res)
    job_doc = nlp(job)
    res_lemmas = {t.lemma_.lower() for t in res_doc if t.pos_ in ("NOUN", "PROPN")}

    candidates = [
        tok.text
        for tok in job_doc
        if tok.pos_ in ("NOUN", "PROPN")
        and tok.is_alpha and not tok.is_stop
        and _looks_like_real_word(tok.text)
    ]

    freq = Counter(w.lower() for w in candidates)
    missing: List[str] = []
    for w, _ in freq.most_common():
        if w not in res_lemmas:
            missing.append(w.title())
        if len(missing) >= top:
            break
    return missing


def _contains_word(line: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}\b", line, flags=re.I) is not None


def _pick_action_verb(bullet: str) -> str | None:
    """Choose a custom action verb or None if already strong."""
    stripped = bullet.lstrip("•▪-*o ").strip()
    if not stripped:
        return None
    fw = stripped.split()[0].rstrip(".,;:").lower()
    if fw in ACTION_VERBS:
        return None
    low = bullet.lower()
    for cue, verb in CUE_TO_VERB.items():
        if cue in low:
            return verb
    return sorted(ACTION_VERBS)[abs(hash(bullet)) % len(ACTION_VERBS)]


def _bullet_notes(line: str, kw: str | None) -> List[str]:
    notes: List[str] = []
    if kw:
        notes.append(f'add "{kw}"')
    verb = _pick_action_verb(line)
    if verb:
        notes.append(f'start with "{verb}"')
    if not DIGIT_RE.search(line):
        notes.append("add number to quantify impact")
    if len(line) > 140:
        notes.append("split into shorter bullet")
    return notes

# --------------------------------------------------------------------------- #
# Core public API
# --------------------------------------------------------------------------- #

def suggest_resume(
    resume_text: str,
    job_text: str,
    top_n_keywords: int = TOP_N_GAPS,
) -> Tuple[str, List[str]]:
    """
    Generate markdown suggestions and missing keywords list.
    """
    # strip out any existing suggestion block
    strip_re = re.compile(
        r"## 🔑 Keywords / Skills to Consider Adding[\s\S]*?## 📄 Revised Resume\n",
        flags=re.MULTILINE,
    )
    resume_text = strip_re.sub("", resume_text, count=1)

    keywords = _keyword_gaps(resume_text, job_text, top_n_keywords)
    remaining = keywords.copy()
    out: List[str] = []

    for line in resume_text.splitlines():
        if CONTACT_RE.search(line) or line.strip().isupper():
            out.append(line)
            continue

        kw_for_line: str | None = None
        if remaining and BULLET_RE.match(line):
            for k in remaining:
                if not _contains_word(line, k):
                    kw_for_line = k
                    remaining.remove(k)
                    break

        notes = _bullet_notes(line, kw_for_line) if BULLET_RE.match(line) else []
        if notes:
            out.append(f"{line}  [{'; '.join(notes)}]")
        else:
            out.append(line)

    header = ["## 🔑 Keywords / Skills to Consider Adding"]
    header += [f"- {k}" for k in keywords] if keywords else ["- NONE"]
    header += ["---", "## 📄 Revised Resume"]

    md = "\n".join(header + out)
    return md, keywords


def suggest_edits(resume_text: str, job_text: str) -> str:
    """Shim for CLI/Streamlit: returns only markdown."""
    md, _ = suggest_resume(resume_text, job_text)
    return md


def markdown_to_pdf(md: str, out_path: str, font_path: str = "DejaVuSans.ttf"):
    """
    Dump the raw markdown into a PDF using a Unicode TTF font so that
    characters like “❖” render correctly.
    """
    from pathlib import Path

    font_path = Path("DejaVuSans.ttf")  # or use absolute path if needed
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVuSans", "", str(font_path), uni=True)
    pdf.set_font("DejaVuSans", "", 12)

    for line in md.splitlines():
        pdf.multi_cell(0, 8, line)

    pdf.output(out_path)
