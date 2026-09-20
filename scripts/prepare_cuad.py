#!/usr/bin/env python3
"""Prepare CUAD open corpus: paragraphs, spans, category descriptions, corpus_stats.

Labels are CUAD human annotations only. License: Atticus CC BY 4.0 (see DATA.md).
"""
from __future__ import annotations

import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "CUAD_v1" / "CUAD_v1.json"
OUT_PARA = ROOT / "data" / "clean" / "paragraphs.jsonl"
OUT_SPANS = ROOT / "data" / "labels" / "spans.jsonl"
OUT_CATS = ROOT / "data" / "clean" / "categories.json"
OUT_STATS = ROOT / "data" / "stats" / "corpus_stats.json"
OUT_CONTRACTS = ROOT / "data" / "clean" / "contracts.jsonl"

# ~400 tokens ≈ 1600 chars; hard cap 2000 chars per chunk
MAX_CHARS = 1600
MIN_CHARS = 80


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def split_paragraphs(context: str, contract_id: str) -> list[dict]:
    """Split contract into paragraph-ish chunks with char offsets.

    Prefer blank-line breaks; merge tiny fragments; split oversized blocks
    on sentence boundaries when possible.
    """
    # Normalize newlines
    text = context.replace("\r\n", "\n").replace("\r", "\n")
    # Find raw blocks by blank lines, fall back to single newlines of length
    raw_blocks: list[tuple[int, int, str]] = []
    for m in re.finditer(r"[^\n]+(?:\n(?!\n)[^\n]+)*", text):
        s, e = m.start(), m.end()
        block = text[s:e].strip()
        if block:
            # recalculate strip offsets roughly
            leading = len(text[s:e]) - len(text[s:e].lstrip())
            trailing = len(text[s:e]) - len(text[s:e].rstrip())
            raw_blocks.append((s + leading, e - trailing, block))

    if not raw_blocks:
        raw_blocks = [(0, len(text), text.strip())]

    chunks: list[tuple[int, int, str]] = []
    buf_s, buf_e, buf_t = None, None, ""

    def flush():
        nonlocal buf_s, buf_e, buf_t
        if buf_t and len(buf_t) >= MIN_CHARS:
            chunks.append((buf_s, buf_e, buf_t))
        elif buf_t and chunks:
            # merge tiny leftover into previous
            ps, pe, pt = chunks[-1]
            chunks[-1] = (ps, buf_e, pt + "\n" + buf_t)
        elif buf_t:
            chunks.append((buf_s, buf_e, buf_t))
        buf_s, buf_e, buf_t = None, None, ""

    for s, e, block in raw_blocks:
        if len(block) > MAX_CHARS:
            flush()
            # sentence-ish split
            parts = re.split(r"(?<=[.?!;:])\s+", block)
            cur, cur_s = "", s
            offset = s
            for part in parts:
                # find part in text starting at offset
                idx = text.find(part, offset)
                if idx < 0:
                    idx = offset
                if cur and len(cur) + 1 + len(part) > MAX_CHARS:
                    chunks.append((cur_s, offset, cur.strip()))
                    cur, cur_s = part, idx
                else:
                    if not cur:
                        cur_s = idx
                    cur = (cur + " " + part).strip() if cur else part
                offset = idx + len(part)
            if cur.strip():
                chunks.append((cur_s, min(offset, e), cur.strip()))
            continue

        if buf_t and len(buf_t) + 1 + len(block) > MAX_CHARS:
            flush()
        if not buf_t:
            buf_s, buf_e, buf_t = s, e, block
        else:
            buf_e = e
            buf_t = buf_t + "\n" + block
    flush()

    out = []
    for i, (s, e, t) in enumerate(chunks):
        out.append(
            {
                "contract_id": contract_id,
                "para_id": f"{contract_id}::p{i:04d}",
                "para_index": i,
                "text": t,
                "char_start": int(s),
                "char_end": int(e),
                "n_chars": len(t),
                "n_tokens_approx": approx_tokens(t),
            }
        )
    return out


def extract_category(question: str, qa_id: str) -> tuple[str, str]:
    m = re.search(r'related to "([^"]+)"', question)
    cat = m.group(1) if m else qa_id.split("__")[-1]
    dm = re.search(r"Details:\s*(.*)$", question, re.S)
    desc = dm.group(1).strip() if dm else question
    return cat, desc


def span_to_paras(span_start: int, span_end: int, paras: list[dict]) -> list[str]:
    hits = []
    for p in paras:
        # overlap
        if p["char_end"] <= span_start or p["char_start"] >= span_end:
            continue
        hits.append(p["para_id"])
    return hits


def main() -> None:
    data = json.loads(RAW.read_text())
    OUT_PARA.parent.mkdir(parents=True, exist_ok=True)
    OUT_SPANS.parent.mkdir(parents=True, exist_ok=True)
    OUT_STATS.parent.mkdir(parents=True, exist_ok=True)

    categories: dict[str, str] = {}
    cat_counts: Counter = Counter()
    para_lens: list[int] = []
    span_lens: list[int] = []
    n_spans = 0
    n_contracts = 0
    n_paras = 0
    n_impossible = 0
    n_possible = 0

    with OUT_PARA.open("w") as fp_para, OUT_SPANS.open("w") as fp_span, OUT_CONTRACTS.open(
        "w"
    ) as fp_c:
        for doc in data["data"]:
            title = doc["title"]
            contract_id = title
            context = doc["paragraphs"][0]["context"]
            paras = split_paragraphs(context, contract_id)
            n_contracts += 1
            n_paras += len(paras)
            for p in paras:
                para_lens.append(p["n_chars"])
                fp_para.write(json.dumps(p, ensure_ascii=False) + "\n")
            fp_c.write(
                json.dumps(
                    {
                        "contract_id": contract_id,
                        "n_chars": len(context),
                        "n_tokens_approx": approx_tokens(context),
                        "n_paragraphs": len(paras),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

            for qa in doc["paragraphs"][0]["qas"]:
                cat, desc = extract_category(qa["question"], qa["id"])
                if cat not in categories:
                    categories[cat] = desc
                if qa.get("is_impossible"):
                    n_impossible += 1
                    continue
                n_possible += 1
                for ai, ans in enumerate(qa.get("answers") or []):
                    text = ans["text"]
                    start = int(ans["answer_start"])
                    end = start + len(text)
                    # verify alignment (CUAD sometimes has whitespace drift)
                    if context[start:end] != text:
                        # search nearby
                        idx = context.find(text, max(0, start - 50), start + len(text) + 50)
                        if idx >= 0:
                            start, end = idx, idx + len(text)
                    para_ids = span_to_paras(start, end, paras)
                    # also store span as its own unit for pairing
                    span_id = f"{qa['id']}::a{ai}"
                    rec = {
                        "span_id": span_id,
                        "contract_id": contract_id,
                        "category": cat,
                        "qa_id": qa["id"],
                        "text": text,
                        "char_start": start,
                        "char_end": end,
                        "n_chars": len(text),
                        "n_tokens_approx": approx_tokens(text),
                        "para_ids": para_ids,
                        "question": qa["question"],
                    }
                    fp_span.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n_spans += 1
                    span_lens.append(len(text))
                    cat_counts[cat] += 1

    OUT_CATS.write_text(json.dumps(categories, indent=2, ensure_ascii=False))

    def pct(xs, p):
        if not xs:
            return None
        ys = sorted(xs)
        i = min(len(ys) - 1, max(0, int(round((p / 100) * (len(ys) - 1)))))
        return ys[i]

    stats = {
        "n_contracts": n_contracts,
        "n_paragraphs": n_paras,
        "n_spans": n_spans,
        "n_possible_qas": n_possible,
        "n_impossible_qas": n_impossible,
        "n_categories": len(categories),
        "tokens_approx_paragraphs": sum(para_lens) // 4,
        "tokens_approx_spans": sum(span_lens) // 4,
        "paragraph_length_chars": {
            "mean": statistics.mean(para_lens) if para_lens else None,
            "p10": pct(para_lens, 10),
            "p50": pct(para_lens, 50),
            "p90": pct(para_lens, 90),
            "p99": pct(para_lens, 99),
            "max": max(para_lens) if para_lens else None,
        },
        "span_length_chars": {
            "mean": statistics.mean(span_lens) if span_lens else None,
            "p10": pct(span_lens, 10),
            "p50": pct(span_lens, 50),
            "p90": pct(span_lens, 90),
            "p99": pct(span_lens, 99),
            "max": max(span_lens) if span_lens else None,
        },
        "category_counts": dict(cat_counts.most_common()),
        "source": "theatticusproject/cuad CUAD_v1.json",
        "license": "CC BY 4.0 (Atticus Project)",
    }
    OUT_STATS.write_text(json.dumps(stats, indent=2))
    # also copy to results later
    print(json.dumps({k: stats[k] for k in ("n_contracts", "n_paragraphs", "n_spans", "n_categories")}, indent=2))
    print("wrote", OUT_PARA, OUT_SPANS, OUT_CATS, OUT_STATS)


if __name__ == "__main__":
    main()
