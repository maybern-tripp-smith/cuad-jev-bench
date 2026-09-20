#!/usr/bin/env python3
"""Render ANALYSIS.md / REPORT.md into the light paper HTML under docs/."""

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
  max-width: 42rem;
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
p { margin: 0.75rem 0; }
.abstract {
  background: #f0ebe3;
  border: 1px solid var(--border);
  padding: 1rem 1.15rem;
  margin: 0 0 1.5rem;
  font-size: 0.98rem;
}
.abstract .label {
  font-family: var(--sans);
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 0 0 0.5rem;
}
.abstract p { margin: 0.55rem 0; }
.abstract p:last-child { margin-bottom: 0; }
table { width: 100%; border-collapse: collapse; font-size: 0.88rem; margin: 1rem 0; font-family: var(--sans); }
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
  max-width: 42rem;
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
    "ANALYSIS.md": "analysis.html",
    "REPORT.md": "report.html",
    "CITATION": "https://github.com/maybern-tripp-smith/cuad-jev-bench/blob/main/CITATION",
}


def rewrite_href(url: str) -> str:
    if url in PAGE_LINKS:
        return PAGE_LINKS[url]
    if url.startswith("results/") or url.startswith("data/"):
        return f"https://github.com/maybern-tripp-smith/cuad-jev-bench/blob/main/{url}"
    return url


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
    text = text.replace("**PASS**", '<span class="pass">PASS</span>')
    text = re.sub(r"> \*\*PASS\*\*", r'> <span class="pass">PASS</span>', text)

    for i, (label, url) in enumerate(links):
        inner = inline_no_link(label)
        href = html.escape(url, quote=True)
        text = text.replace(f"\x00L{i}\x00", f'<a href="{href}">{inner}</a>')
    for i, code in enumerate(codes):
        text = text.replace(f"\x00C{i}\x00", f"<code>{code}</code>")
    text = text.replace("<strong>PASS</strong>", '<span class="pass">PASS</span>')
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


def md_to_html(md: str, *, drop_h1: bool = True, abstract_box: bool = False) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    in_abstract = False
    n = len(lines)
    skipped_h1 = False

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
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if level == 1 and drop_h1 and not skipped_h1:
                skipped_h1 = True
                i += 1
                continue
            if title == "Abstract" and abstract_box:
                if in_abstract:
                    out.append("</div>")
                    in_abstract = False
                out.append('<div class="abstract">')
                out.append('<p class="label">Abstract</p>')
                in_abstract = True
                i += 1
                continue
            if in_abstract:
                out.append("</div>")
                in_abstract = False
            tag = f"h{level}"
            out.append(f"<{tag}>{inline(title)}</{tag}>")
            i += 1
            continue
        img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", line)
        if img:
            alt, src = img.group(1), img.group(2)
            if src.startswith("results/figures/"):
                src = "figures/" + src.split("results/figures/", 1)[1]
            cap = None
            j = i + 1
            if j < n and not lines[j].strip():
                j += 1
            if j < n and re.match(r"^\*.+\*\s*$", lines[j].strip()):
                cap = lines[j].strip()[1:-1].strip()
                i = j + 1
            else:
                i += 1
            block = ['<figure>']
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
        while i < n and lines[i].strip() and not re.match(r"^(#{1,3}\s+|```|\||---$|[-*]\s+|\d+\.\s+|> )", lines[i]):
            para.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(para)) + "</p>")
        if in_abstract and i < n and re.match(r"^#{1,3}\s+", lines[i] if i < n else ""):
            out.append("</div>")
            in_abstract = False
    if in_abstract:
        out.append("</div>")
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
    h = f"<h1 class=\"page\">{html.escape(heading)}</h1>\n" if heading else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Pre-registered evaluation of TypeSafe/Jev on FOMC chair openings (cuad-jev-2026-09-20).">
<meta http-equiv="Cache-Control" content="no-cache">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400&display=swap">
<style>
{CSS}
</style>
</head>
<body>
<header>
<p class="kicker">Technical report · run cuad-jev-2026-09-20</p>
<h1>cuad-jev-bench</h1>
<p>Contract-clause relevance on CUAD: pairwise Choice and graded Score under a frozen criterion</p>
</header>
<nav>
{" ".join(nav)}
</nav>
<main>
{h}{body}
</main>
<footer>
Research instrumentation only. CUAD text is CC BY 4.0 (Atticus Project). Companion repository:
<a href="{REPO}">maybern-tripp-smith/cuad-jev-bench</a>.

</footer>
</body>
</html>
"""


def index_body() -> str:
    return """
<div class="abstract">
<p class="label">Abstract</p>
<p>Human annotations of contract clauses are a natural but incomplete label for relevance to a requested legal category. Nearby paragraphs often share vocabulary without being on-point.</p>
<p>This note reports a pre-registered evaluation of TypeSafe/Jev on the open CUAD corpus under the fixed criterion <code>more relevant to the requested contract category</code>. Primary quantities are reported with standard errors (s.e.). Gate 4 is a construct-validity contrast: mean Score on gold spans versus BM25 hard-negatives under the same category query. Gate 7 cites published DeBERTa extractive metrics for difficulty context only and does not re-run DeBERTa.</p>
</div>

<h2>Measurement</h2>
<p>Two constructs are distinguished. The annotation measure is recovery of human CUAD spans. The relevance measure is pairwise Choice and graded Score against hard negatives under a fixed category description.</p>
<p>Gates 1, 3 (signal), 4, and 6 are pre-registered pass/fail or signal tests. Gates 2, 5, and 7 are report-only.</p>

<h2>Selected estimates</h2>
<table>
<thead><tr><th>Gate</th><th>Estimate</th></tr></thead>
<tbody>
<tr><td>1 Easy-pair inversion</td><td><span class="pass">PASS</span> — 0.000 (n=40, s.e. 0.000)</td></tr>
<tr><td>3 Candidate MRR (Jev vs BM25)</td><td><span class="pass">PASS_SIGNAL</span> — 0.917 (s.e. 0.021) &gt; 0.469 (s.e. 0.041)</td></tr>
<tr><td>4 Construct validity (Score gap)</td><td><span class="pass">PASS</span> — 2.130 (s.e. 0.067)</td></tr>
<tr><td>6 Name/meta stability</td><td><span class="pass">PASS</span> — Δ inversion = 0.000</td></tr>
<tr><td>7 Literature DeBERTa</td><td>report only — not a re-run</td></tr>
</tbody>
</table>

<h2>Selected figures</h2>
<figure>
<img src="figures/inversion_rates.svg" alt="Inversion rates by stratum">
<figcaption>Choice inversion rates ± binomial standard error for Stratum A (n=40) and Stratum B (n=200). Dashed line: Gate 1 threshold (0.05).</figcaption>
</figure>
<figure>
<img src="figures/gold_vs_neg_scores.svg" alt="Gold versus hard-negative Score means">
<figcaption>Gate 4 construct validity: mean expected Score on gold spans versus BM25 hard-negatives ± standard error.</figcaption>
</figure>
<figure>
<img src="figures/mrr_recall_vs_baselines.svg" alt="MRR and Recall versus baselines">
<figcaption>Gold MRR and Recall@k under Jev Score, BM25, and chance (± s.e. where defined).</figcaption>
</figure>

<h2>Documents</h2>
<ul>
<li><a href="analysis.html">Analysis</a> — methods, results, figures, limitations</li>
<li><a href="report.html">Report</a> — gate tables, cost, and artifacts</li>
<li>Machine-readable: <code>results/gates.json</code>, <code>results/diagnostics.json</code></li>
</ul>
"""



def main() -> None:
    analysis_md = (ROOT / "ANALYSIS.md").read_text()
    report_md = (ROOT / "REPORT.md").read_text()
    analysis_html = md_to_html(analysis_md, drop_h1=True, abstract_box=True)
    report_html = md_to_html(report_md, drop_h1=True, abstract_box=True)

    (DOCS / "index.html").write_text(
        page("cuad-jev-bench — Overview", "index", index_body().strip())
    )
    (DOCS / "analysis.html").write_text(
        page(
            "cuad-jev-bench — Analysis",
            "analysis",
            analysis_html,
            heading="Analysis",
        )
    )
    (DOCS / "report.html").write_text(
        page(
            "cuad-jev-bench — Report",
            "report",
            report_html,
            heading="Report",
        )
    )
    print("wrote docs/index.html docs/analysis.html docs/report.html")


if __name__ == "__main__":
    main()
