#!/usr/bin/env python3
"""Build frozen gold pairs for cuad-jev-bench (Design A + candidate-score lite).

Stratum A (n=40): gold span vs clearly unrelated paragraph from another
category/contract — rule-built, no taste. Must-not-invert.
Stratum B (n≤200): gold span vs BM25 hard-negative from same contract
(or same-category pool) that is NOT the gold span. Seed 20260920.
Candidate queries (n_q=100): (contract, category) with ≥1 gold span;
BM25 top-10 over paragraph chunks with gold injection if missing.

Writes:
  data/pairs/gold_pairs.jsonl
  data/pairs/candidate_queries.jsonl
  data/pairs/PAIR_MANIFEST.md
  results/preflight_cost.json

Does NOT call Jev.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20260920
N_A = 40
N_B = 200
N_Q = 100
TOP_K = 10
PRICE_PER_MTOK = 0.042
AVG_TOK_CHOICE = 900  # rough
AVG_TOK_SCORE = 700

# Categories that are mostly short named entities / dates — poorer for A "certain"
META_CATS = {
    "Document Name",
    "Agreement Date",
    "Effective Date",
    "Expiration Date",
    "Parties",
}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open() if l.strip()]


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def build_bm25(docs: list[str]):
    from rank_bm25 import BM25Okapi

    corpus = [tokenize(d) for d in docs]
    return BM25Okapi(corpus), corpus


def main() -> None:
    rng = random.Random(SEED)
    spans = load_jsonl(ROOT / "data" / "labels" / "spans.jsonl")
    paras = load_jsonl(ROOT / "data" / "clean" / "paragraphs.jsonl")
    categories = json.loads((ROOT / "data" / "clean" / "categories.json").read_text())

    para_by_id = {p["para_id"]: p for p in paras}
    paras_by_contract: dict[str, list[dict]] = defaultdict(list)
    for p in paras:
        paras_by_contract[p["contract_id"]].append(p)

    spans_by_cat: dict[str, list[dict]] = defaultdict(list)
    spans_by_contract: dict[str, list[dict]] = defaultdict(list)
    for s in spans:
        spans_by_cat[s["category"]].append(s)
        spans_by_contract[s["contract_id"]].append(s)

    # Index: which para_ids contain gold for (contract, category)
    gold_paras: dict[tuple[str, str], set[str]] = defaultdict(set)
    gold_spans_cc: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for s in spans:
        key = (s["contract_id"], s["category"])
        gold_spans_cc[key].append(s)
        for pid in s.get("para_ids") or []:
            gold_paras[key].add(pid)

    # ---------- Stratum A: certain pairs ----------
    # Rule: gold span text (category C) vs a paragraph that (i) is from a different
    # contract, (ii) does not overlap any span of category C in that other contract,
    # (iii) is from a contract that has no annotation for C (impossible or absent),
    # (iv) length within [0.5x, 2x] of gold chars when possible.
    # Prefer substantive categories (not META_CATS).
    substantive_cats = [c for c in categories if c not in META_CATS and spans_by_cat[c]]
    # contracts with / without each category
    contracts_with_cat: dict[str, set[str]] = defaultdict(set)
    for s in spans:
        contracts_with_cat[s["category"]].add(s["contract_id"])
    all_contracts = set(paras_by_contract.keys())

    a_candidates = []
    for cat in substantive_cats:
        without = list(all_contracts - contracts_with_cat[cat])
        if not without:
            continue
        for gold in spans_by_cat[cat]:
            if gold["n_chars"] < 40 or gold["n_chars"] > 1200:
                continue
            # pick a random other contract without this category
            other_c = rng.choice(without)
            other_paras = paras_by_contract[other_c]
            if not other_paras:
                continue
            # pick paragraph farthest in length band, prefer mid-length
            target = gold["n_chars"]
            scored = []
            for p in other_paras:
                if p["n_chars"] < 60:
                    continue
                # reject if this para is a gold span for ANY category that matches
                # our gold text exactly (unlikely) — keep simple: just length
                ratio = p["n_chars"] / max(1, target)
                if 0.4 <= ratio <= 2.5:
                    scored.append(p)
            if not scored:
                scored = [p for p in other_paras if p["n_chars"] >= 60] or other_paras
            neg = rng.choice(scored)
            a_candidates.append((cat, gold, neg))

    rng.shuffle(a_candidates)
    # diversify categories
    picked_a = []
    from collections import Counter

    used_cats = Counter()
    for cat, gold, neg in a_candidates:
        if used_cats[cat] >= 3:
            continue
        picked_a.append((cat, gold, neg))
        used_cats[cat] += 1
        if len(picked_a) >= N_A:
            break
    # fill if short
    if len(picked_a) < N_A:
        for cat, gold, neg in a_candidates:
            if (cat, gold["span_id"], neg["para_id"]) in {
                (c, g["span_id"], n["para_id"]) for c, g, n in picked_a
            }:
                continue
            picked_a.append((cat, gold, neg))
            if len(picked_a) >= N_A:
                break

    pairs: list[dict] = []
    # materialize pair texts into a unit index
    units: dict[str, dict] = {}

    def register_unit(uid: str, text: str, meta: dict) -> str:
        if uid not in units:
            units[uid] = {"unit_id": uid, "text": text, **meta}
        return uid

    for i, (cat, gold, neg) in enumerate(picked_a[:N_A], start=1):
        pair_id = f"A{i:03d}"
        a_id = register_unit(
            f"span:{gold['span_id']}",
            gold["text"],
            {
                "kind": "span",
                "contract_id": gold["contract_id"],
                "category": cat,
                "span_id": gold["span_id"],
            },
        )
        b_id = register_unit(
            f"para:{neg['para_id']}",
            neg["text"],
            {
                "kind": "paragraph",
                "contract_id": neg["contract_id"],
                "para_id": neg["para_id"],
            },
        )
        pairs.append(
            {
                "pair_id": pair_id,
                "stratum": "A",
                "a": a_id,
                "b": b_id,
                "gold": "a",
                "source": "certain_cross_contract",
                "confidence": "certain",
                "category": cat,
                "category_description": categories[cat],
                "seed": SEED,
            }
        )

    # ---------- Stratum B: BM25 hard negatives ----------
    # For each gold span, BM25-rank other paragraphs in same contract; take top
    # non-overlapping as hard neg. Cap 200, seed-fixed sample.
    b_pool = []
    for cat in categories:
        for gold in spans_by_cat[cat]:
            if gold["n_chars"] < 30:
                continue
            cparas = paras_by_contract[gold["contract_id"]]
            if len(cparas) < 3:
                continue
            gold_pids = set(gold.get("para_ids") or [])
            docs = [p["text"] for p in cparas]
            try:
                bm25, _ = build_bm25(docs)
            except Exception:
                continue
            q = tokenize(gold["text"] + " " + cat + " " + categories[cat])
            if not q:
                continue
            scores = bm25.get_scores(q)
            ranked = sorted(range(len(cparas)), key=lambda i: -scores[i])
            neg = None
            for idx in ranked:
                p = cparas[idx]
                if p["para_id"] in gold_pids:
                    continue
                # also skip if paragraph heavily overlaps gold char range
                if gold_pids and p["para_id"] in gold_pids:
                    continue
                # char overlap with gold
                if not (
                    p["char_end"] <= gold["char_start"] or p["char_start"] >= gold["char_end"]
                ):
                    continue
                if p["n_chars"] < 40:
                    continue
                neg = p
                break
            if neg is None:
                continue
            b_pool.append((cat, gold, neg, float(scores[ranked[0]] if ranked else 0)))

    rng.shuffle(b_pool)
    # diversify
    used_b_cats = Counter()
    used_contracts = Counter()
    picked_b = []
    for cat, gold, neg, sc in b_pool:
        if used_b_cats[cat] >= 12:
            continue
        if used_contracts[gold["contract_id"]] >= 4:
            continue
        picked_b.append((cat, gold, neg))
        used_b_cats[cat] += 1
        used_contracts[gold["contract_id"]] += 1
        if len(picked_b) >= N_B:
            break
    if len(picked_b) < N_B:
        for cat, gold, neg, sc in b_pool:
            key = (gold["span_id"], neg["para_id"])
            if key in {(g["span_id"], n["para_id"]) for _, g, n in picked_b}:
                continue
            picked_b.append((cat, gold, neg))
            if len(picked_b) >= N_B:
                break

    for i, (cat, gold, neg) in enumerate(picked_b[:N_B], start=1):
        pair_id = f"B{i:03d}"
        a_id = register_unit(
            f"span:{gold['span_id']}",
            gold["text"],
            {
                "kind": "span",
                "contract_id": gold["contract_id"],
                "category": cat,
                "span_id": gold["span_id"],
            },
        )
        b_id = register_unit(
            f"para:{neg['para_id']}",
            neg["text"],
            {
                "kind": "paragraph",
                "contract_id": neg["contract_id"],
                "para_id": neg["para_id"],
            },
        )
        pairs.append(
            {
                "pair_id": pair_id,
                "stratum": "B",
                "a": a_id,
                "b": b_id,
                "gold": "a",
                "source": "bm25_hard_neg_same_contract",
                "confidence": "labeled",
                "category": cat,
                "category_description": categories[cat],
                "seed": SEED,
            }
        )

    # ---------- Candidate queries ----------
    eligible_keys = [k for k, v in gold_spans_cc.items() if len(v) >= 1]
    rng.shuffle(eligible_keys)
    # diversify categories
    used_q_cats = Counter()
    query_keys = []
    for k in eligible_keys:
        cat = k[1]
        if used_q_cats[cat] >= 8:
            continue
        # need enough paragraphs
        if len(paras_by_contract[k[0]]) < 5:
            continue
        query_keys.append(k)
        used_q_cats[cat] += 1
        if len(query_keys) >= N_Q:
            break
    if len(query_keys) < N_Q:
        for k in eligible_keys:
            if k in query_keys:
                continue
            if len(paras_by_contract[k[0]]) < 5:
                continue
            query_keys.append(k)
            if len(query_keys) >= N_Q:
                break

    queries = []
    for qi, (cid, cat) in enumerate(query_keys[:N_Q], start=1):
        cparas = paras_by_contract[cid]
        docs = [p["text"] for p in cparas]
        bm25, _ = build_bm25(docs)
        # query = category name + description
        q = tokenize(cat + " " + categories[cat])
        scores = bm25.get_scores(q)
        ranked_idx = sorted(range(len(cparas)), key=lambda i: -scores[i])
        top = ranked_idx[:TOP_K]
        top_pids = [cparas[i]["para_id"] for i in top]
        gold_pids = list(gold_paras[(cid, cat)])
        # prefer gold para that overlaps the longest gold span
        gspans = gold_spans_cc[(cid, cat)]
        gspans_sorted = sorted(gspans, key=lambda s: -s["n_chars"])
        primary_gold_pids = gspans_sorted[0].get("para_ids") or []
        injected = False
        candidates = list(top_pids)
        gold_in_top = [pid for pid in primary_gold_pids if pid in candidates]
        if not gold_in_top and primary_gold_pids:
            # inject first gold para at end (or replace last)
            inj = primary_gold_pids[0]
            if inj in para_by_id:
                if len(candidates) >= TOP_K:
                    candidates[-1] = inj
                else:
                    candidates.append(inj)
                injected = True
                gold_in_top = [inj]
        elif not gold_in_top:
            # fall back: any gold para for this cc
            for pid in gold_pids:
                if pid in para_by_id:
                    if len(candidates) >= TOP_K:
                        candidates[-1] = pid
                    else:
                        candidates.append(pid)
                    injected = True
                    gold_in_top = [pid]
                    break

        # BM25 rank of first gold (1-indexed); None if missing before inject
        bm25_rank = None
        for rank, idx in enumerate(ranked_idx, start=1):
            if cparas[idx]["para_id"] in (primary_gold_pids or gold_pids):
                bm25_rank = rank
                break

        # register candidate units
        cand_units = []
        for pid in candidates:
            uid = register_unit(
                f"para:{pid}",
                para_by_id[pid]["text"],
                {
                    "kind": "paragraph",
                    "contract_id": cid,
                    "para_id": pid,
                },
            )
            cand_units.append(uid)

        queries.append(
            {
                "query_id": f"Q{qi:03d}",
                "contract_id": cid,
                "category": cat,
                "category_description": categories[cat],
                "candidate_unit_ids": cand_units,
                "candidate_para_ids": candidates,
                "gold_para_ids": gold_in_top or primary_gold_pids[:1],
                "all_gold_para_ids": list(gold_pids),
                "bm25_rank_first_gold": bm25_rank,
                "gold_injected": injected,
                "n_candidates": len(candidates),
                "seed": SEED,
            }
        )

    # Write units + pairs + queries
    pairs_dir = ROOT / "data" / "pairs"
    pairs_dir.mkdir(parents=True, exist_ok=True)
    units_path = pairs_dir / "units.jsonl"
    with units_path.open("w") as f:
        for u in units.values():
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

    gold_path = pairs_dir / "gold_pairs.jsonl"
    with gold_path.open("w") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    q_path = pairs_dir / "candidate_queries.jsonl"
    with q_path.open("w") as f:
        for q in queries:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    # Manifest
    n_a = sum(1 for p in pairs if p["stratum"] == "A")
    n_b = sum(1 for p in pairs if p["stratum"] == "B")
    cat_hist_a = Counter(p["category"] for p in pairs if p["stratum"] == "A")
    cat_hist_b = Counter(p["category"] for p in pairs if p["stratum"] == "B")
    cat_hist_q = Counter(q["category"] for q in queries)

    manifest = f"""# PAIR_MANIFEST — cuad-jev-2026-09-20

**Frozen before any Jev call.** Seed `{SEED}`.

## Criterion (exact)

`more relevant to the requested contract category`

## Counts

| Set | n |
|-----|--:|
| Stratum A (certain, cross-contract unrelated) | {n_a} |
| Stratum B (BM25 hard-neg, same contract) | {n_b} |
| Candidate queries (Score top-10) | {len(queries)} |
| Unique text units | {len(units)} |

## Construction rules

### Stratum A
For category C (prefer non-meta categories), pair a CUAD gold span text against a
paragraph from a **different** contract that has **no** human annotation for C.
Length band ≈ 0.4–2.5× gold when available. Gold side is always `a`. Rule-built;
no human taste ranking among candidates beyond seeded RNG among rule-eligible set.

### Stratum B
For a gold span, BM25-rank paragraphs of the **same** contract with query =
span text + category + description; select the highest-scoring paragraph that
does not overlap the gold char span. Cap {N_B}; diversify categories (≤12) and
contracts (≤4). Seed `{SEED}`.

### Candidate queries
Sample {N_Q} (contract, category) pairs with ≥1 gold span and ≥5 paragraphs.
BM25 over paragraph chunks (~≤400 tok) with query = category + description;
take top-{TOP_K}. If no gold paragraph appears in top-{TOP_K}, inject one gold
paragraph (logged as `gold_injected`) so rank under Jev Score is measurable.
Injection is **not** counted as BM25 retrieval success.

## Category histograms

### A
{json.dumps(dict(cat_hist_a.most_common()), indent=2)}

### B
{json.dumps(dict(cat_hist_b.most_common()), indent=2)}

### Queries
{json.dumps(dict(cat_hist_q.most_common()), indent=2)}

## Files

- `data/pairs/gold_pairs.jsonl`
- `data/pairs/candidate_queries.jsonl`
- `data/pairs/units.jsonl`
- `data/pairs/PAIR_MANIFEST.md` (this file)
"""
    (pairs_dir / "PAIR_MANIFEST.md").write_text(manifest)

    # Preflight cost
    n_choice = (n_a + n_b) * 2  # both orders
    n_choice_ablation = n_a * 2  # Gate 6 names-in
    n_score = sum(q["n_candidates"] for q in queries)
    est_tok_choice = n_choice * AVG_TOK_CHOICE
    est_tok_ablation = n_choice_ablation * AVG_TOK_CHOICE
    est_tok_score = n_score * AVG_TOK_SCORE
    est_tok = est_tok_choice + est_tok_ablation + est_tok_score
    est_usd = est_tok * PRICE_PER_MTOK / 1e6
    preflight = {
        "run_id": "cuad-jev-2026-09-20",
        "seed": SEED,
        "n_stratum_a": n_a,
        "n_stratum_b": n_b,
        "n_queries": len(queries),
        "n_choice_calls_main": n_choice,
        "n_choice_calls_ablation": n_choice_ablation,
        "n_score_calls": n_score,
        "n_calls_total_est": n_choice + n_choice_ablation + n_score,
        "avg_tok_choice_assumed": AVG_TOK_CHOICE,
        "avg_tok_score_assumed": AVG_TOK_SCORE,
        "est_input_tokens": est_tok,
        "est_usd": round(est_usd, 5),
        "price_per_mtok_input": PRICE_PER_MTOK,
        "target_budget_usd": 0.15,
        "under_budget": est_usd < 0.15,
    }
    (ROOT / "results").mkdir(parents=True, exist_ok=True)
    (ROOT / "results" / "preflight_cost.json").write_text(json.dumps(preflight, indent=2))
    print(json.dumps(preflight, indent=2))
    print("gold frozen ->", gold_path)


if __name__ == "__main__":
    main()
