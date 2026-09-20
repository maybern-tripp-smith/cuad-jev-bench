"""Strip party names, dates, and filing furniture from contract text for judge calls.

Keeps semantic clause content; raw_text retained for Gate 6 name/meta ablation.
"""
from __future__ import annotations

import re

# Common date patterns
DATE_PAT = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b",
    re.I,
)
ISO_DATE = re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b")
US_DATE = re.compile(r"\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b")
# "as of Month Day, Year"
AS_OF = re.compile(
    r"\bas of\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4}\b",
    re.I,
)

# Corporate suffixes used to detect party-like proper names (heuristic)
CORP = re.compile(
    r"\b([A-Z][A-Za-z0-9&'’.\-]+(?:\s+[A-Z][A-Za-z0-9&'’.\-]+){0,5}\s+"
    r"(?:Inc\.?|LLC|L\.?L\.?C\.?|Corp\.?|Corporation|Ltd\.?|Limited|L\.?P\.?|"
    r"Company|Co\.|PLC|N\.?A\.?|LLP))\b"
)

# "Party A" / defined-party quotes: "Acme" means ...
DEFINED_PARTY = re.compile(
    r'["""]([A-Z][^"""]{1,60})["""]\s*(?:\(|means|shall mean)',
)

# SEC filing furniture
FURNITURE = re.compile(
    r"^(?:EXHIBIT\s+\d[\d.A-Z]*|Page\s+\d+\s+of\s+\d+|TABLE OF CONTENTS)\s*$",
    re.I | re.M,
)

# Email / URL / phone (identity leak)
EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")
URL = re.compile(r"https?://\S+|www\.\S+", re.I)
PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")


def strip_meta(text: str) -> str:
    if not text:
        return ""
    out = FURNITURE.sub("", text)
    out = AS_OF.sub("as of [DATE]", out)
    out = DATE_PAT.sub("[DATE]", out)
    out = ISO_DATE.sub("[DATE]", out)
    out = US_DATE.sub("[DATE]", out)
    out = CORP.sub("[PARTY]", out)
    out = DEFINED_PARTY.sub(r'"[PARTY]" means', out)
    out = EMAIL.sub("[EMAIL]", out)
    out = URL.sub("[URL]", out)
    out = PHONE.sub("[PHONE]", out)
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


if __name__ == "__main__":
    import sys

    print(strip_meta(sys.stdin.read()))
