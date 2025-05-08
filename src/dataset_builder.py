from pathlib import Path
import json, typer

app = typer.Typer()

def _join(lst, sep=" • "):
    """
    Flatten a list of strings, dropping empties/dupes and skipping non-strings.
    """
    seen = set()
    out = []
    for v in lst:
        if not isinstance(v, str):
            continue
        v = v.strip()
        if not v:
            continue
        key = v.lower()
        if key in seen:
            continue
        out.append(v)
        seen.add(key)
    return sep.join(out)

def _entry_to_text(e: dict) -> str:
    name = e.get("name", "UNKNOWN")
    abilities = _join(e.get("abilities", []))
    skills    = _join(e.get("skills", []))

    # education entries have 'program' and 'institution'
    edu = []
    for ed in e.get("education", []):
        prog = ed.get("program") or ""
        inst = ed.get("institution") or ""
        if prog or inst:
            edu.append(f"{prog} – {inst}".strip(" – "))
    education = "; ".join(edu)

    # experience entries have 'title', 'firm', 'start_date', 'end_date'
    xp = []
    for ex in e.get("experience", []):
        title = ex.get("title") or ""
        firm  = ex.get("firm") or ""
        sd    = ex.get("start_date") or ""
        edd   = ex.get("end_date") or ""
        part = f"{title} @ {firm} ({sd}–{edd})".strip()
        xp.append(part)
    experience = "; ".join(xp)

    return (
        f"NAME: {name}\n"
        f"ABILITIES: {abilities}\n"
        f"SKILLS: {skills}\n"
        f"EDUCATION: {education}\n"
        f"EXPERIENCE: {experience}\n"
    )

@app.command("build-json")
def build_json(
    json_file: Path = typer.Argument(..., help="Path to Parsed Resume.json"),
    out: Path       = typer.Option(Path("data/pairs.jsonl"), help="Output JSONL path"),
):
    out.parent.mkdir(parents=True, exist_ok=True)
    data = json.load(open(json_file, encoding="utf-8"))
    total = 0
    with open(out, "w", encoding="utf-8") as fo:
        for rid, entry in data.items():
            text = _entry_to_text(entry)
            # input==target for self-supervised use
            json.dump({"input": text, "target": text}, fo)
            fo.write("\n")
            total += 1
    typer.echo(f"[dataset_builder] Wrote {total} records to {out}")

if __name__ == "__main__":
    app()
