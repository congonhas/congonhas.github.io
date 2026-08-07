#!/usr/bin/env python3
"""
Turn papers.bib into the HTML fragments the site includes.

This is the only moving part of the whole site. It runs automatically before
every render (see the `pre-render` line in _quarto.yml), so the workflow for
adding a paper is: edit papers.bib, save, done.

No third-party libraries on purpose. It runs anywhere Python 3 runs, including
on GitHub's servers, with nothing to install and nothing to break.

Outputs:
  _selected.html   the five curated papers on the homepage
  _research.html   working papers, publications, older working papers
"""

import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BIB = os.path.join(HERE, "papers.bib")

TOPICS = [
    ("early", "Early childhood"),
    ("beliefs", "Parental beliefs"),
    ("meas", "Measurement &amp; econometrics"),
    ("ineq", "Inequality &amp; mobility"),
    ("edu", "Education policy"),
]

SECTIONS = [("wp", "Working papers"), ("pub", "Publications"), ("old", "Older working papers")]

# Topic filter buttons and the "Download all BibTeX" link above the paper list.
# Currently off: the research page is just the three lists. Set this to True to
# bring both back; the JavaScript that drives the filters is still in
# _footer.html and does nothing while there is no filter bar to click.
SHOW_FILTERS = False


# --------------------------------------------------------------------------
# A small BibTeX reader. Handles @type{key, field = {value}, ...} with nested
# braces and quoted values. It does not try to be a general BibTeX engine; it
# reads the subset this site uses.
# --------------------------------------------------------------------------
def parse_bib(text):
    entries = []
    i = 0
    n = len(text)
    while True:
        at = text.find("@", i)
        if at == -1:
            break
        m = re.match(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text[at:])
        if not m:
            i = at + 1
            continue
        etype, key = m.group(1).lower(), m.group(2)
        pos = at + m.end()
        depth = 1
        start = pos
        while pos < n and depth > 0:
            c = text[pos]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            pos += 1
        body = text[start:pos - 1]
        entries.append({"_type": etype, "_key": key, **parse_fields(body)})
        i = pos
    return entries


def parse_fields(body):
    fields = {}
    i, n = 0, len(body)
    while i < n:
        m = re.compile(r"\s*(\w+)\s*=\s*").match(body, i)
        if not m:
            break
        name = m.group(1).lower()
        i = m.end()
        if i < n and body[i] == "{":
            depth, j = 1, i + 1
            while j < n and depth:
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                j += 1
            value = body[i + 1:j - 1]
            i = j
        elif i < n and body[i] == '"':
            j = body.find('"', i + 1)
            value = body[i + 1:j]
            i = j + 1
        else:
            j = body.find(",", i)
            j = n if j == -1 else j
            value = body[i:j]
            i = j
        fields[name] = " ".join(value.split())
        comma = body.find(",", i)
        i = n if comma == -1 else comma + 1
    return fields


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
TEX = {
    r"\&": "&", r"\%": "%", r"\$": "$", r"\_": "_", r"\#": "#",
    "--": "\u2013", "---": "\u2014", "``": "\u201c", "''": "\u201d",
}
TEX_ACCENT = re.compile(r"\\([`'^\"~=.cv])\{?(\w)\}?")
ACCENTS = {
    "`": "\u0300", "'": "\u0301", "^": "\u0302", '"': "\u0308",
    "~": "\u0303", "=": "\u0304", ".": "\u0307", "c": "\u0327", "v": "\u030c",
}


def detex(s):
    """Turn the LaTeX escapes BibTeX allows into plain Unicode."""
    import unicodedata
    if not s:
        return s
    s = s.replace("---", "\u2014").replace("--", "\u2013")
    s = TEX_ACCENT.sub(lambda m: unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)]), s)
    for a, b in TEX.items():
        s = s.replace(a, b)
    return s.replace("{", "").replace("}", "")


def esc(s):
    return html.escape(detex(s) or "", quote=False)


def authors(raw):
    """BibTeX 'A and B and C' becomes 'A, B, C'."""
    parts = [p.strip() for p in re.split(r"\s+and\s+", raw or "") if p.strip()]
    out = []
    for p in parts:
        if "," in p:                       # 'Cunha, Flavio' -> 'Flavio Cunha'
            last, first = p.split(",", 1)
            p = f"{first.strip()} {last.strip()}"
        out.append(p)
    return ", ".join(out)


def link_row(e):
    """Bracketed secondary links, in a fixed order so every entry reads alike."""
    order = [
        ("doi", "Journal", lambda v: v if v.startswith("http") else "https://doi.org/" + v),
        ("nber", "NBER", lambda v: v if v.startswith("http") else "https://www.nber.org/papers/" + v),
        ("pdf", "PDF", lambda v: v),
        ("appendix", "Appendix", lambda v: v),
        ("code", "Replication package", lambda v: v),
        ("summary", "Summary", lambda v: v),
    ]
    out = []
    for field, label, fix in order:
        if e.get(field):
            out.append(f'<a href="{esc(fix(e[field]))}" target="_blank" rel="noopener">{label}</a>')
    out.append(f'<a href="bibtex/{esc(e["_key"])}.bib">BibTeX</a>')
    return "".join(out)


def venue(e):
    """The italic line under the title."""
    if e.get("venue"):
        return e["venue"]
    bits = []
    if e.get("journal"):
        bits.append(e["journal"])
        vol = e.get("volume", "")
        if vol:
            vol += f"({e['number']})" if e.get("number") else ""
            bits.append(vol)
        if e.get("pages"):
            bits.append(e["pages"])
    elif e.get("booktitle"):
        bits.append("In " + e["booktitle"])
        if e.get("chapter"):
            bits.append("ch. " + e["chapter"])
        if e.get("pages"):
            bits.append(e["pages"])
        if e.get("publisher"):
            bits.append(e["publisher"])
    return ", ".join(bits)


def best_url(e):
    if e.get("url"):
        return e["url"]
    if e.get("pdf"):
        return e["pdf"]
    if e.get("nber"):
        v = e["nber"]
        return v if v.startswith("http") else "https://www.nber.org/papers/" + v
    if e.get("doi"):
        v = e["doi"]
        return v if v.startswith("http") else "https://doi.org/" + v
    return ""


def entry_html(e, uid):
    url = best_url(e)
    title = esc(e.get("title", "Untitled"))
    t = (f'<a href="{esc(url)}" target="_blank" rel="noopener">{title}</a>'
         if url else f"<span>{title}</span>")

    v = venue(e)
    line = f'{esc(authors(e.get("author", "")))} &middot; {esc(v)}'
    if e.get("year") and e["year"] not in v:
        line += f' &middot; {esc(e["year"])}'

    badges = ""
    if e.get("status"):
        badges += f'<span class="status">{esc(e["status"])}</span>'
    if e.get("abstract"):
        badges += f'<button class="abs-toggle" data-target="abs-{uid}">Show abstract</button>'
    badges += link_row(e)

    abstract = ""
    if e.get("abstract"):
        abstract = f'<div class="abs" id="abs-{uid}"><p>{esc(e["abstract"])}</p></div>'

    topics = " ".join("t-" + t.strip() for t in (e.get("topics") or "").split(",") if t.strip())
    return (f'<div class="paper {topics}">\n'
            f'  <p class="t">{t}</p>\n'
            f'  <p class="m">{line}</p>\n'
            f'  <div class="badges">{badges}</div>\n'
            f'  {abstract}\n'
            f'</div>')


def sort_key(e):
    return (-int(e.get("sortyear") or e.get("year") or 0), e.get("_order", 0))


def main():
    if not os.path.exists(BIB):
        sys.exit(f"build_papers.py: cannot find {BIB}")

    with open(BIB, encoding="utf-8") as fh:
        entries = parse_bib(fh.read())
    for i, e in enumerate(entries):
        e["_order"] = i

    # --- research page -----------------------------------------------------
    parts = []
    if SHOW_FILTERS:
        filters = ['<div class="filters">',
                   '<span class="tools"><a href="all-papers.bib">Download all BibTeX</a></span>',
                   '<button class="on" data-topic="all">All</button>']
        for key, label in TOPICS:
            filters.append(f'<button data-topic="t-{key}">{label}</button>')
        filters.append("</div>")
        parts.append("\n".join(filters))

    uid = 0
    for cat, heading in SECTIONS:
        rows = sorted([e for e in entries if e.get("category") == cat], key=sort_key)
        if not rows:
            continue
        parts.append(f'<h2 class="sec">{heading}</h2>')
        parts.append(f'<div class="paper-group" data-group="{cat}">')
        for e in rows:
            uid += 1
            parts.append(entry_html(e, uid))
        parts.append("</div>")
    write("_research.html", "\n".join(parts))

    # --- homepage ----------------------------------------------------------
    sel = sorted([e for e in entries if (e.get("selected") or "").lower() in ("yes", "true")],
                 key=sort_key)
    out = []
    for e in sel:
        uid += 1
        out.append(entry_html(e, uid))
    write("_selected.html", "\n".join(out))

    # --- per-paper and combined BibTeX ------------------------------------
    bibdir = os.path.join(HERE, "bibtex")
    os.makedirs(bibdir, exist_ok=True)
    combined = []
    with open(BIB, encoding="utf-8") as fh:
        raw = fh.read()
    for e in entries:
        block = extract_raw(raw, e["_key"])
        combined.append(block)
        with open(os.path.join(bibdir, e["_key"] + ".bib"), "w", encoding="utf-8") as fh:
            fh.write(block + "\n")
    with open(os.path.join(HERE, "all-papers.bib"), "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(combined) + "\n")

    print(f"build_papers.py: {len(entries)} papers, {len(sel)} selected")


def extract_raw(text, key):
    """Pull one entry back out of the file verbatim, for the BibTeX downloads."""
    m = re.search(r"@\w+\s*\{\s*" + re.escape(key) + r"\s*,", text)
    if not m:
        return ""
    i, depth = m.end(), 1
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[m.start():i]


def write(name, content):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
        fh.write(content + "\n")


if __name__ == "__main__":
    main()
