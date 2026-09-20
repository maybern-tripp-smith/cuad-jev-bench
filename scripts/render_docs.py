#!/usr/bin/env python3
"""Render OVERVIEW.md / ANALYSIS.md / REPORT.md into the light paper HTML under docs/."""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

CSS = r"""
:root {
  --bg: #f7f5f0;
  --paper: #ffffff;
  --text: #1a1a1a;
  --muted: #4a5568;
  --accent: #1a365d;
  --border: #d4cfc4;
  --pass: #276749;
  --serif: "Source Serif 4", "Palatino Linotype", Palatino, "Times New Roman", Times, serif;
  --sans: "IBM Plex Sans", "Helvetica Neue", Helvetica, Arial, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: var(--serif);
  background: var(--bg);
  color: var(--text);
  line-height: 1.65;
  font-size: 17px;
}
header {
  background: var(--paper);
  border-bottom: 1px solid var(--border);
  padding: 2rem 1.5rem 1.25rem;
}
header .kicker {
  font-family: var(--sans);
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 0 0 0.5rem;
}
header h1 {
  font-family: var(--serif);
  font-weight: 600;
  font-size: 1.75rem;
  margin: 0 0 0.4rem;
  letter-spacing: -0.02em;
}
header p { margin: 0; color: var(--muted); font-size: 0.95rem; font-family: var(--sans); }
nav {
  display: flex; gap: 1.25rem; flex-wrap: wrap;
  padding: 0.65rem 1.5rem;
  background: var(--paper);
  border-bottom: 1px solid var(--border);
  font-family: var(--sans);
  font-size: 0.88rem;
}
nav a { color: var(--accent); text-decoration: none; }
nav a.active { font-weight: 600; border-bottom: 2px solid var(--accent); }
main {
  max-width: 48rem;
  margin: 0 auto;
  padding: 2rem 1.25rem 3rem;
  background: var(--paper);
  border-left: 1px solid var(--border);
  border-right: 1px solid var(--border);
  min-height: 70vh;
}
h1.page { font-size: 1.45rem; margin: 0 0 1rem; font-weight: 600; }
h2 {
  font-size: 1.15rem;
  margin: 2rem 0 0.75rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid var(--border);
  font-weight: 600;
}
h3 { font-size: 1.02rem; margin: 1.35rem 0 0.5rem; font-weight: 600; }
h4 { font-size: 0.96rem; margin: 1.1rem 0 0.4rem; font-weight: 600; }
p { margin: 0.75rem 0; }
.abstract, .howto {
  border: 1px solid var(--border);
  padding: 1rem 1.15rem;
  margin: 0 0 1.5rem;
  font-size: 0.98rem;
}
.abstract { background: #f0ebe3; }
.howto { background: #eef2f6; }
.abstract .label, .howto .label {
  font-family: var(--sans);
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 0 0 0.5rem;
}
.abstract p, .howto p { margin: 0.55rem 0; }
.abstract p:last-child, .howto p:last-child { margin-bottom: 0; }
.howto ol { margin: 0.4rem 0 0.2rem; }
table { width: 100%; border-collapse: collapse; font-size: 0.86rem; margin: 1rem 0; font-family: var(--sans); }
th, td { border: 1px solid var(--border); padding: 0.45rem 0.55rem; text-align: left; vertical-align: top; }
th { background: #f0ebe3; font-weight: 600; }
code, pre { font-family: var(--mono); font-size: 0.84rem; }
code { background: #f0ebe3; padding: 0.1em 0.3em; }
pre { background: #f0ebe3; padding: 1rem; overflow: auto; border: 1px solid var(--border); }
pre code { background: none; padding: 0; }
blockquote {
  margin: 1rem 0;
  padding: 0.35rem 1rem;
  border-left: 3px solid var(--accent);
  color: var(--muted);
}
.pass { color: var(--pass); font-weight: 600; font-family: var(--sans); }
ul, ol { padding-left: 1.25rem; }
li { margin: 0.35rem 0; }
footer {
  max-width: 48rem;
  margin: 0 auto;
  padding: 1.25rem;
  color: var(--muted);
  font-size: 0.82rem;
  font-family: var(--sans);
  border-left: 1px solid var(--border);
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  background: var(--paper);
}
a { color: var(--accent); }
.meta { font-family: var(--sans); font-size: 0.88rem; color: var(--muted); }
figure { margin: 1.5rem 0 1.75rem; }
figure img {
  width: 100%;
  height: auto;
  border: 1px solid var(--border);
  background: #ffffff;
  display: block;
}
figcaption {
  font-size: 0.88rem;
  color: var(--muted);
  margin: 0.5rem 0 0;
  line-height: 1.5;
}
"""

REPO = "https://github.com/maybern-tripp-smith/cuad-jev-bench"

PAGE_LINKS = {
    "OVERVIEW.md": "index.html",
    "ANALYSIS.md": "analysis.html",
    "REPORT.md": "report.html",
    "CITATION": f"{REPO}/blob/main/CITATION",
}

BOX_HEADINGS = {
    "Abstract": "abstract",
    "How to read this report": "howto",
    "How to read this analysis": "howto",
    "Terms used in this report": "howto",
}

META_DESCRIPTION = (
    "Pre-registered TypeSafe/Jev evaluation of contract-clause relevance "
    "on the Contract Understanding Atticus Dataset (run cuad-jev-2026-09-20)."
)


def heading_id(title: str) -> str:
    text = re.sub(r"[*`]", "", title)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def rewrite_href(url: str) -> str:
    if url in PAGE_LINKS:
        return PAGE_LINKS[url]
    if url.startswith("results/") or url.startswith("data/"):
        return f"{REPO}/blob/main/{url}"
    return url


def rewrite_img_src(src: str) -> str:
    if src.startswith("./"):
        src = src[2:]
    if src.startswith("docs/figures/"):
        return src[len("docs/") :]
    if src.startswith("results/figures/"):
        return "figures/" + src.split("results/figures/", 1)[1]
    return src


def inline(text: str) -> str:
    """Convert a subset of Markdown inline syntax. Placeholders protect code spans."""
    codes: list[str] = []

    def stash_code(m: re.Match[str]) -> str:
        codes.append(html.escape(m.group(1)))
        return f"\x00C{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash_code, text)

    links: list[tuple[str, str]] = []

    def stash_link(m: re.Match[str]) -> str:
        label, url = m.group(1), rewrite_href(m.group(2))
        links.append((label, url))
        return f"\x00L{len(links) - 1}\x00"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", stash_link, text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)

    for i, (label, url) in enumerate(links):
        inner = inline_no_link(label)
        href = html.escape(url, quote=True)
        text = text.replace(f"\x00L{i}\x00", f'<a href="{href}">{inner}</a>')
    for i, code in enumerate(codes):
        text = text.replace(f"\x00C{i}\x00", f"<code>{code}</code>")
    text = text.replace("<strong>PASS</strong>", '<span class="pass">PASS</span>')
    text = text.replace("<strong>PASS_SIGNAL</strong>", '<span class="pass">PASS_SIGNAL</span>')
    return text


def inline_no_link(text: str) -> str:
    codes: list[str] = []

    def stash_code(m: re.Match[str]) -> str:
        codes.append(html.escape(m.group(1)))
        return f"\x00C{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash_code, text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    for i, code in enumerate(codes):
        text = text.replace(f"\x00C{i}\x00", f"<code>{code}</code>")
    return text


def parse_table(lines: list[str]) -> str:
    rows = []
    for line in lines:
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cols)
    header, body = rows[0], rows[2:]
    out = ["<table><thead><tr>"]
    out.extend(f"<th>{inline(c)}</th>" for c in header)
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        out.extend(f"<td>{inline(c)}</td>" for c in row)
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def md_to_html(md: str, *, drop_h1: bool = True) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    in_box: str | None = None
    n = len(lines)
    skipped_h1 = False

    def close_box() -> None:
        nonlocal in_box
        if in_box:
            out.append("</div>")
            in_box = None

    while i < n:
        line = lines[i]
        if line.strip() == "---":
            i += 1
            continue
        if line.startswith("```"):
            fence = []
            i += 1
            while i < n and not lines[i].startswith("```"):
                fence.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(fence)) + "</code></pre>")
            continue
        if line.startswith("|") and i + 1 < n and re.match(r"^\|?\s*-+", lines[i + 1]):
            table_lines = [line]
            i += 1
            while i < n and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            out.append(parse_table(table_lines))
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if level == 1 and drop_h1 and not skipped_h1:
                skipped_h1 = True
                i += 1
                continue
            box_class = BOX_HEADINGS.get(title)
            if box_class:
                close_box()
                hid = heading_id(title)
                out.append(f'<div class="{box_class}" id="{html.escape(hid, quote=True)}">')
                out.append(f'<p class="label">{inline(title)}</p>')
                in_box = box_class
                i += 1
                continue
            if in_box:
                close_box()
            hid = heading_id(title)
            tag = f"h{level}"
            out.append(f'<{tag} id="{html.escape(hid, quote=True)}">{inline(title)}</{tag}>')
            i += 1
            continue
        img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", line)
        if img:
            alt, src = img.group(1), rewrite_img_src(img.group(2))
            cap = None
            j = i + 1
            if j < n and not lines[j].strip():
                j += 1
            if j < n and re.match(r"^\*.+\*\s*$", lines[j].strip()):
                cap = lines[j].strip()[1:-1].strip()
                i = j + 1
            else:
                i += 1
            block = ["<figure>"]
            block.append(
                f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}">'
            )
            if cap:
                block.append(f"<figcaption>{inline(cap)}</figcaption>")
            block.append("</figure>")
            out.append("\n".join(block))
            continue
        if line.startswith("> "):
            quote = [line[2:]]
            i += 1
            while i < n and lines[i].startswith("> "):
                quote.append(lines[i][2:])
                i += 1
            out.append("<blockquote>" + inline(" ".join(quote)) + "</blockquote>")
            continue
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < n and re.match(r"^[-*]\s+", lines[i]):
                items.append("<li>" + inline(re.sub(r"^[-*]\s+", "", lines[i])) + "</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i]):
                items.append("<li>" + inline(re.sub(r"^\d+\.\s+", "", lines[i])) + "</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue
        if not line.strip():
            i += 1
            continue
        para = [line]
        i += 1
        while i < n and lines[i].strip() and not re.match(
            r"^(#{1,4}\s+|```|\||---$|[-*]\s+|\d+\.\s+|> )", lines[i]
        ):
            para.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(para)) + "</p>")
        if in_box and i < n and re.match(r"^#{1,4}\s+", lines[i] if i < n else ""):
            close_box()
    close_box()
    return "\n".join(out)


def page(
    title: str,
    active: str,
    body: str,
    *,
    heading: str | None = None,
) -> str:
    nav = []
    for href, label, key in (
        ("index.html", "Overview", "index"),
        ("analysis.html", "Analysis", "analysis"),
        ("report.html", "Report", "report"),
    ):
        cls = ' class="active"' if key == active else ""
        nav.append(f'<a href="{href}"{cls}>{label}</a>')
    nav.append(f'<a href="{REPO}">GitHub</a>')
    h = f'<h1 class="page">{html.escape(heading)}</h1>\n' if heading else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{html.escape(META_DESCRIPTION, quote=True)}">
<meta http-equiv="Cache-Control" content="no-cache">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
{CSS}
</style>
</head>
<body>
<header>
<p class="kicker">Pre-registered evaluation · run cuad-jev-2026-09-20</p>
<h1>cuad-jev-bench</h1>
<p>A contract-clause relevance test on the Atticus public contracts, written so a non-specialist can rebuild it</p>
</header>
<nav>
{" ".join(nav)}
</nav>
<main>
{h}{body}
</main>
<footer>
Research instrumentation only. Contract Understanding Atticus Dataset text is CC BY 4.0 (Atticus Project). Companion repository:
<a href="{REPO}">maybern-tripp-smith/cuad-jev-bench</a>.

</footer>
</body>
</html>
"""


def main() -> None:
    overview_md = (ROOT / "OVERVIEW.md").read_text()
    analysis_md = (ROOT / "ANALYSIS.md").read_text()
    report_md = (ROOT / "REPORT.md").read_text()

    (DOCS / "index.html").write_text(
        page("cuad-jev-bench — Overview", "index", md_to_html(overview_md, drop_h1=True))
    )
    (DOCS / "analysis.html").write_text(
        page(
            "cuad-jev-bench — Analysis",
            "analysis",
            md_to_html(analysis_md, drop_h1=True),
            heading="Analysis",
        )
    )
    (DOCS / "report.html").write_text(
        page(
            "cuad-jev-bench — Report",
            "report",
            md_to_html(report_md, drop_h1=True),
            heading="Report",
        )
    )
    print("wrote docs/index.html docs/analysis.html docs/report.html")


if __name__ == "__main__":
    main()
