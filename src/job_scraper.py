import requests, trafilatura, re

STOP = re.compile(r"(?i)equal opportunity|EEO|background check")

def fetch(url: str) -> str:
    html = requests.get(url, timeout=10).text
    txt  = trafilatura.extract(html, include_comments=False) or ""
    lines = [l.strip() for l in txt.splitlines() if l.strip() and not STOP.search(l)]
    return "\n".join(lines[:2000])