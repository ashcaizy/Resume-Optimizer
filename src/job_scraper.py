import re
import json
import cloudscraper
from bs4 import BeautifulSoup
import trafilatura

# Optional JavaScript rendering fallback
try:
    from requests_html import HTMLSession
    _js_session = HTMLSession()
    _have_js = True
except ImportError:
    _have_js = False

_scraper = cloudscraper.create_scraper()
STOP = re.compile(r"(?i)equal opportunity|EEO|background check")

def _get_html(url: str, timeout: int = 10) -> str:
    r = _scraper.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text

def _try_next_data_extract(soup) -> str:
    """Try to extract job description from a __NEXT_DATA__ JSON script."""
    tag = soup.find("script", id="__NEXT_DATA__", type="application/json")
    if not tag:
        return ""
    try:
        data = json.loads(tag.string)
        # Heuristically find the first long string value in the JSON tree
        def find_texts(obj):
            if isinstance(obj, str) and len(obj) > 100:
                yield obj
            elif isinstance(obj, list):
                for x in obj:
                    yield from find_texts(x)
            elif isinstance(obj, dict):
                for v in obj.values():
                    yield from find_texts(v)
        candidates = list(find_texts(data))
        return max(candidates, key=len) if candidates else ""
    except Exception:
        return ""

def _fallback_bs_extract(soup) -> str:
    """Fallback: try to get all text from most content-rich tag."""
    candidates = soup.find_all(['section', 'article', 'div'])
    best = max(candidates, key=lambda tag: len(tag.get_text()), default=None)
    return best.get_text(separator="\n") if best else ""

def fetch(url: str) -> str:
    html = _get_html(url)
    soup = BeautifulSoup(html, "html.parser")

    # 1. Try Trafilatura
    txt = trafilatura.extract(html, include_comments=False) or ""

    # 2. Try extracting from Next.js JSON
    if not txt:
        txt = _try_next_data_extract(soup)

    # 3. Fallback to general soup extraction
    if not txt:
        txt = _fallback_bs_extract(soup)

    # 4. Last-resort: JS render fallback
    if not txt and _have_js:
        r = _js_session.get(url)
        r.html.render(timeout=20)
        txt = r.html.full_text or ""

    # Filter out boilerplate and blank lines
    lines = [line.strip() for line in txt.splitlines() if line.strip() and not STOP.search(line)]
    return "\n".join(lines[:2000])

