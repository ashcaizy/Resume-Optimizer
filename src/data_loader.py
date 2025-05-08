from pathlib import Path
import pdfplumber
import docx

def read_file(path: str | Path) -> str:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        # extract each page’s text (with line breaks)
        pages = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        text = "\n".join(pages)

    elif suffix in {".docx", ".doc"}:
        # extract each paragraph (preserves manual line breaks)
        doc = docx.Document(path)
        paras = [p.text for p in doc.paragraphs]
        text = "\n".join(paras)

    else:
        # plain text file
        text = path.read_text(encoding="utf-8")

    # normalize line endings & strip trailing spaces, but keep blank lines
    lines = text.splitlines()
    cleaned = [ln.rstrip() for ln in lines]
    return "\n".join(cleaned)
