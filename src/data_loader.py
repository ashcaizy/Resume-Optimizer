from pathlib import Path
import pdfplumber, docx, re

def _clean(txt: str) -> str:
    return re.sub(r"\s+", " ", txt).strip()

def read_file(path: str | Path) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        with pdfplumber.open(path) as pdf:
            text = " ".join((page.extract_text() or "") for page in pdf.pages)
    elif suffix in {".docx", ".doc"}:
        doc = docx.Document(path)
        text = " ".join(p.text for p in doc.paragraphs)
    else:
        text = path.read_text(encoding="utf-8")
    return _clean(text)