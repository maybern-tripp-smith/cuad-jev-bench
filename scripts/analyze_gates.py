#!/usr/bin/env python3
"""Compute gates, cost, timing, accuracy for cuad-jev-bench."""
from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "cuad-jev-2026-09-20"
CRITERION = "more relevant to the requested contract category"
PRICE = 0.042
SEED = 20260920


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.open() if l.strip()]


def ste(xs: list[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    return float(np.std(xs, ddof=1) / math.sqrt(len(xs)))


def bootstrap_mean_ste(xs: list[float], n_boot: int = 1000, seed: int = SEED) -> tuple[float, float]:
    if not xs:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    boots = []
    n = len(xs)
    for _ in range(n_boot):
        sample = [xs[rng.randrange(n)] for _ in range(n)]
        boots.append(sum(sample) / n)
    return float(np.mean(xs)), float(np.std(boots, ddof=1))


def ece(probs: list[float], labels: list[int], n_bins: int = 10) -> float:
    """Expected calibration error for binary outcomes with predicted p(positive)."""
    if not probs:
        return float("nan")
    bins = defaultdict(list)
    for p, y in zip(probs, labels):
        b = min(n_bins - 1, int(p * n_bins))
        bins[b].append((p, y))
    total = len(probs)
    err = 0.0
    for items in bins.values():
        if not items:
            continue
        conf = sum(p for p, _ in items) / len(items)
        acc = sum(y for _, y in items) / len(items)
        err += (len(items) / total) * abs(acc - conf)
    return err


def pair_p_gold(rec_ab: dict, rec_ba: dict, gold: str) -> tuple[float, str, bool]:
    """Average both orders onto p(gold side wins). gold is 'a' or 'b' in pair space."""
    # In order ab: Text A = pair.a, Text B = pair.b
    # In order ba: Text A = pair.b, Text B = pair.a  (so p_A in ba = p(pair.b))
    if gold == "a":
        p_ab = float(rec_ab.get("p_A") or 0.0)  # P(pair.a)
        p_ba = float(rec_ba.get("p_B") or 0.0)  # P(pair.a) when shown as B
    else:
        p_ab = float(rec_ab.get("p_B") or 0.0)
        p_ba = float(rec_ba.get("p_A") or 0.0)
    p = 0.5 * (p_ab + p_ba)
    # winners in pair-space
    win_ab = "a" if rec_ab.get("winner") == "A" else "b"
    win_ba = "b" if rec_ba.get("winner") == "A" else "a"  # A in ba display is pair.b
    # averaged winner by p
    winner = "a" if p >= 0.5 else "b"
    inverted = winner != gold
    order_flip = win_ab != win_ba
    return p, winner, inverted, order_flip


def analyze_pairs(answers: list[dict], mode: str = "stripped") -> dict[str, Any]:
    by_pair: dict[str, dict[str, dict]] = defaultdict(dict)
    for a in answers:
        if a.get("kind") != "choice" or not a.get("ok"):
            continue
        if a.get("mode") != mode:
            continue
        by_pair[a["pair_id"]][a["order"]] = a

    pairs_meta = {p["pair_id"]: p for p in load_jsonl(ROOT / "data" / "pairs" / "gold_pairs.jsonl")}
    judgments = []
    by_stratum: dict[str, list] = defaultdict(list)

    for pid, orders in by_pair.items():
        if "ab" not in orders or "ba" not in orders:
            continue
        meta = pairs_meta.get(pid, {})
        gold = meta.get("gold", "a")
        p, winner, inverted, order_flip = pair_p_gold(orders["ab"], orders["ba"], gold)
        brier = (p - 1.0) ** 2  # gold is always correct label = 1
        # actually if we define y=1 for gold, predicted p(gold)
        row = {
            "pair_id": pid,
            "stratum": meta.get("stratum"),
            "category": meta.get("category"),
            "gold": gold,
            "p_gold": p,
            "winner": winner,
            "inverted": inverted,
            "order_flip": order_flip,
            "brier": brier,
            "mode": mode,
            "model": orders["ab"].get("model"),
        }
        judgments.append(row)
        by_stratum[meta.get("stratum", "?")].append(row)

    summary = {}
    for s, rows in by_stratum.items():
        inv = [1.0 if r["inverted"] else 0.0 for r in rows]
        briers = [r["brier"] for r in rows]
        pgs = [r["p_gold"] for r in rows]
        flips = [1.0 if r["order_flip"] else 0.0 for r in rows]
        inv_mean, inv_ste = bootstrap_mean_ste(inv)
        br_mean, br_ste = bootstrap_mean_ste(briers)
        summary[s] = {
            "n": len(rows),
            "n_inverted": int(sum(inv)),
            "inversion": inv_mean,
            "inversion_ste": inv_ste,
            "mean_p_gold": float(np.mean(pgs)),
            "mean_brier": br_mean,
            "brier_ste": br_ste,
            "order_flip_rate": float(np.mean(flips)),
            "inverted_ids": [r["pair_id"] for r in rows if r["inverted"]],
        }
    return {"judgments": judgments, "by_stratum": summary}


def expected_score(prob: dict, legend: dict) -> float:
    """Map probabilities to 0..3 expected level index using legend."""
    # legend maps index -> level name OR level name -> index depending on SDK
    # fedjev used ans.score directly; we also have score field
    return None  # unused


def analyze_candidates(answers: list[dict]) -> dict[str, Any]:
    queries = {q["query_id"]: q for q in load_jsonl(ROOT / "data" / "pairs" / "candidate_queries.jsonl")}
    by_q: dict[str, list[dict]] = defaultdict(list)
    for a in answers:
        if a.get("kind") != "score" or not a.get("ok"):
            continue
        by_q[a["query_id"]].append(a)

    rows = []
    mrr_jev = []
    mrr_bm25 = []
    r_at = {1: [], 3: [], 5: []}
    r_bm25 = {1: [], 3: [], 5: []}
    gold_scores = []
    neg_scores = []
    chance_mrr = []

    for qid, scores in by_q.items():
        q = queries.get(qid)
        if not q:
            continue
        gold_set = set(q.get("gold_para_ids") or [])
        # sort by expected score descending
        scored = []
        for s in scores:
            pid = s.get("para_id")
            sc = float(s.get("score") or 0.0)
            scored.append((sc, pid, s))
            if pid in gold_set or s.get("is_gold"):
                gold_scores.append(sc)
            else:
                neg_scores.append(sc)
        scored.sort(key=lambda x: -x[0])
        # gold rank under Jev
        gold_rank = None
        for i, (sc, pid, s) in enumerate(scored, start=1):
            if pid in gold_set or s.get("is_gold"):
                gold_rank = i
                break
        if gold_rank is None:
            continue
        mrr_jev.append(1.0 / gold_rank)
        for k in r_at:
            r_at[k].append(1.0 if gold_rank <= k else 0.0)

        bm25_rank = q.get("bm25_rank_first_gold")
        if bm25_rank is None:
            # treat as worse than n_candidates
            bm25_rank_eff = max(len(scored) + 1, 11)
            mrr_bm25.append(0.0)
        else:
            bm25_rank_eff = int(bm25_rank)
            mrr_bm25.append(1.0 / bm25_rank_eff)
        for k in r_bm25:
            r_bm25[k].append(1.0 if bm25_rank is not None and bm25_rank <= k else 0.0)

        n_c = len(scored)
        # chance: expected MRR if gold uniform among n_c
        chance_mrr.append(sum(1.0 / r for r in range(1, n_c + 1)) / n_c)

        for rank, (sc, pid, s) in enumerate(scored, start=1):
            rows.append(
                {
                    "query_id": qid,
                    "category": q["category"],
                    "contract_id": q["contract_id"],
                    "para_id": pid,
                    "unit_id": s.get("unit_id"),
                    "score": sc,
                    "is_gold": bool(pid in gold_set or s.get("is_gold")),
                    "rank_jev": rank,
                    "bm25_rank_first_gold": bm25_rank,
                    "gold_injected": q.get("gold_injected"),
                    "confidence": s.get("confidence"),
                }
            )

    def mean_ste(xs):
        if not xs:
            return {"mean": None, "ste": None, "n": 0}
        m, s = bootstrap_mean_ste(xs)
        return {"mean": m, "ste": s, "n": len(xs)}

    summary = {
        "n_queries_scored": len(mrr_jev),
        "jev_mrr": mean_ste(mrr_jev),
        "bm25_mrr": mean_ste(mrr_bm25),
        "chance_mrr": mean_ste(chance_mrr),
        "jev_recall": {f"@{k}": mean_ste(r_at[k]) for k in r_at},
        "bm25_recall": {f"@{k}": mean_ste(r_bm25[k]) for k in r_bm25},
        "mean_score_gold": mean_ste(gold_scores),
        "mean_score_neg": mean_ste(neg_scores),
        "signal_jev_mrr_gt_bm25": (
            (float(np.mean(mrr_jev)) > float(np.mean(mrr_bm25))) if mrr_jev and mrr_bm25 else None
        ),
        "construct_gold_gt_neg": (
            (float(np.mean(gold_scores)) > float(np.mean(neg_scores)))
            if gold_scores and neg_scores
            else None
        ),
    }
    # gap STE via bootstrap of difference
    if gold_scores and neg_scores:
        rng = random.Random(SEED)
        gaps = []
        for _ in range(1000):
            g = [gold_scores[rng.randrange(len(gold_scores))] for _ in range(len(gold_scores))]
            n = [neg_scores[rng.randrange(len(neg_scores))] for _ in range(len(neg_scores))]
            gaps.append(sum(g) / len(g) - sum(n) / len(n))
        summary["score_gap"] = {
            "mean": float(np.mean(gold_scores) - np.mean(neg_scores)),
            "ste": float(np.std(gaps, ddof=1)),
        }
    return {"rows": rows, "summary": summary}


def cost_timing(answers: list[dict]) -> tuple[dict, dict]:
    by = defaultdict(lambda: {
        "n_calls": 0,
        "n_cache_hits": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "latencies": [],
    })
    for a in answers:
        if not a.get("ok"):
            continue
        if a.get("kind") == "choice":
            key = f"choice_{a.get('mode')}_{a.get('stratum')}"
        else:
            key = "score_candidates"
        b = by[key]
        b["n_calls"] += 1
        if a.get("cache_hit"):
            b["n_cache_hits"] += 1
        else:
            b["input_tokens"] += int(a.get("input_tokens") or 0)
            b["output_tokens"] += int(a.get("output_tokens") or 0)
            b["latencies"].append(int(a.get("latency_ms") or 0))

    cost = {"run_id": RUN_ID, "price_per_mtok_input": PRICE, "by_stratum": {}, "total": {}}
    timing = {"run_id": RUN_ID, "by_stratum": {}, "total": {}}
    tot_in = tot_out = tot_calls = tot_cache = 0
    all_lat = []
    for k, b in by.items():
        usd = b["input_tokens"] * PRICE / 1e6
        cost["by_stratum"][k] = {
            "n_calls": b["n_calls"],
            "n_cache_hits": b["n_cache_hits"],
            "input_tokens": b["input_tokens"],
            "output_tokens": b["output_tokens"],
            "usd": round(usd, 6),
        }
        lats = b["latencies"]
        if lats:
            timing["by_stratum"][k] = {
                "n": len(lats),
                "mean_ms": float(np.mean(lats)),
                "p50_ms": float(np.percentile(lats, 50)),
                "p95_ms": float(np.percentile(lats, 95)),
            }
            all_lat.extend(lats)
        tot_in += b["input_tokens"]
        tot_out += b["output_tokens"]
        tot_calls += b["n_calls"]
        tot_cache += b["n_cache_hits"]

    cost["total"] = {
        "n_calls": tot_calls,
        "n_cache_hits": tot_cache,
        "input_tokens": tot_in,
        "output_tokens": tot_out,
        "usd": round(tot_in * PRICE / 1e6, 6),
    }
    if all_lat:
        timing["total"] = {
            "n": len(all_lat),
            "mean_ms": float(np.mean(all_lat)),
            "p50_ms": float(np.percentile(all_lat, 50)),
            "p95_ms": float(np.percentile(all_lat, 95)),
        }
    return cost, timing


def main() -> None:
    answers = load_jsonl(ROOT / "runs" / "jev" / "answers.jsonl")
    # dedupe: keep last ok per (kind, pair_id/order/mode) or (query, unit)
    dedup: dict[str, dict] = {}
    for a in answers:
        if a.get("kind") == "choice":
            key = f"c|{a.get('pair_id')}|{a.get('order')}|{a.get('mode')}"
        elif a.get("kind") == "score":
            key = f"s|{a.get('query_id')}|{a.get('unit_id')}"
        else:
            continue
        dedup[key] = a
    answers = list(dedup.values())

    pair_stripped = analyze_pairs(answers, mode="stripped")
    pair_names = analyze_pairs(answers, mode="names_in")
    cand = analyze_candidates(answers)
    cost, timing = cost_timing(answers)

    # write judgments
    jpath = ROOT / "results" / "pair_judgments.jsonl"
    with jpath.open("w") as f:
        for row in pair_stripped["judgments"] + pair_names["judgments"]:
            f.write(json.dumps(row) + "\n")

    cpath = ROOT / "results" / "candidate_scores.csv"
    with cpath.open("w", newline="") as f:
        if cand["rows"]:
            w = csv.DictWriter(f, fieldnames=list(cand["rows"][0].keys()))
            w.writeheader()
            w.writerows(cand["rows"])

    # Gate metrics
    a = pair_stripped["by_stratum"].get("A", {})
    b = pair_stripped["by_stratum"].get("B", {})
    a_names = pair_names["by_stratum"].get("A", {})
    inv_a = a.get("inversion", float("nan"))
    inv_a_names = a_names.get("inversion", float("nan"))
    delta_inv = abs(inv_a_names - inv_a) if a and a_names else float("nan")

    # ECE / Brier on B
    b_rows = [r for r in pair_stripped["judgments"] if r["stratum"] == "B" and r["mode"] == "stripped"]
    brier_vals = [r["brier"] for r in b_rows]
    ece_val = ece([r["p_gold"] for r in b_rows], [1] * len(b_rows))

    literature = {
        "model": "DeBERTa-xlarge (published CUAD extractive QA)",
        "citation": (
            "Hendrycks et al., CUAD: An Expert-Annotated NLP Dataset for Legal Contract Review, "
            "NeurIPS 2021 Datasets & Benchmarks. https://arxiv.org/abs/2103.06268"
        ),
        "metrics": {
            "AUPR": 47.8,
            "P_at_80_recall": 44.0,
            "P_at_90_recall": 17.8,
            "Jaccard_ge_0.5": "reported in paper / leaderboard context",
        },
        "note": (
            "Literature extractive SOTA cited for difficulty narrative only. "
            "This bench does NOT re-run DeBERTa. Task shape differs: candidate Score / pairwise "
            "Choice vs extractive span QA."
        ),
        "jaccard_ge_0.5_source": "CUAD paper / Atticus leaderboard reporting for DeBERTa-xlarge",
    }
    # CUAD paper Table: DeBERTa-xlarge AUPR 47.8, Precision@80%Recall 44.0, Precision@90%Recall 17.8
    # Jaccard is often reported on leaderboard; keep as qualitative cite
    literature["metrics"]["Jaccard_ge_0.5"] = (
        "See CUAD paper / https://www.atticusprojectai.org/ — extractive overlap metric; "
        "not recomputed here"
    )

    cs = cand["summary"]
    gates = {
        "run_id": RUN_ID,
        "criterion": CRITERION,
        "model_requested": "jev-latest",
        "model_resolved": next(
            (a.get("model") for a in answers if a.get("model")), "jev-1.13.0"
        ),
        "gates": {
            "1_easy_pair_inversion": {
                "metric": inv_a,
                "ste": a.get("inversion_ste"),
                "n": a.get("n"),
                "pass_line": 0.05,
                "result": "PASS" if inv_a is not None and inv_a <= 0.05 else "FAIL",
                "inverted_ids": a.get("inverted_ids", []),
            },
            "2_labeled_pair_inversion_brier": {
                "inversion": b.get("inversion"),
                "inversion_ste": b.get("inversion_ste"),
                "brier": b.get("mean_brier"),
                "brier_ste": b.get("brier_ste"),
                "mean_p_gold": b.get("mean_p_gold"),
                "n": b.get("n"),
                "result": "report",
            },
            "3_candidate_score_vs_bm25": {
                "jev_mrr": cs["jev_mrr"],
                "bm25_mrr": cs["bm25_mrr"],
                "chance_mrr": cs["chance_mrr"],
                "jev_recall": cs["jev_recall"],
                "bm25_recall": cs["bm25_recall"],
                "signal_jev_mrr_gt_bm25": cs["signal_jev_mrr_gt_bm25"],
                "result": (
                    "PASS_SIGNAL"
                    if cs["signal_jev_mrr_gt_bm25"]
                    else ("FAIL_SIGNAL" if cs["signal_jev_mrr_gt_bm25"] is False else "report")
                ),
            },
            "4_construct_validity": {
                "mean_score_gold": cs["mean_score_gold"],
                "mean_score_neg": cs["mean_score_neg"],
                "gap": cs.get("score_gap"),
                "gold_gt_neg": cs["construct_gold_gt_neg"],
                "result": "PASS" if cs["construct_gold_gt_neg"] else "FAIL",
            },
            "5_secondary_calibration": {
                "brier_stratum_b": float(np.mean(brier_vals)) if brier_vals else None,
                "brier_ste": ste(brier_vals) if brier_vals else None,
                "ece_stratum_b": ece_val,
                "n": len(brier_vals),
                "result": "report",
            },
            "6_name_meta_ablation": {
                "inversion_stripped": inv_a,
                "inversion_names_in": inv_a_names,
                "delta_inversion": delta_inv,
                "pass_line": 0.05,
                "result": "PASS" if delta_inv <= 0.05 else "FAIL",
                "n": a_names.get("n"),
            },
            "7_literature_deberta": {
                **literature,
                "result": "report",
            },
        },
        "strata_summary": pair_stripped["by_stratum"],
        "names_in_summary": pair_names["by_stratum"],
    }

    accuracy = {
        "run_id": RUN_ID,
        "inversion_A": a,
        "inversion_B": b,
        "candidate": {
            "mrr_jev": cs["jev_mrr"],
            "mrr_bm25": cs["bm25_mrr"],
            "mrr_chance": cs["chance_mrr"],
            "recall_jev": cs["jev_recall"],
            "recall_bm25": cs["bm25_recall"],
            "mean_score_gold": cs["mean_score_gold"],
            "mean_score_neg": cs["mean_score_neg"],
            "score_gap": cs.get("score_gap"),
        },
        "calibration_B": {
            "brier": gates["gates"]["5_secondary_calibration"]["brier_stratum_b"],
            "ece": ece_val,
        },
        "ablation_delta_inversion": delta_inv,
    }

    # data_stats from corpus + pair counts
    corpus = json.loads((ROOT / "data" / "stats" / "corpus_stats.json").read_text())
    data_stats = {
        **corpus,
        "n_pairs_A": a.get("n"),
        "n_pairs_B": b.get("n"),
        "n_candidate_queries": cs["n_queries_scored"],
        "n_candidate_score_rows": len(cand["rows"]),
    }

    out = ROOT / "results"
    (out / "gates.json").write_text(json.dumps(gates, indent=2))
    (out / "cost.json").write_text(json.dumps(cost, indent=2))
    (out / "timing.json").write_text(json.dumps(timing, indent=2))
    (out / "data_stats.json").write_text(json.dumps(data_stats, indent=2))
    (out / "accuracy_summary.json").write_text(json.dumps(accuracy, indent=2))
    (out / "baseline_literature.json").write_text(json.dumps(literature, indent=2))

    print(json.dumps({
        "gate1": gates["gates"]["1_easy_pair_inversion"]["result"],
        "inv_A": inv_a,
        "inv_B": b.get("inversion"),
        "gate3": gates["gates"]["3_candidate_score_vs_bm25"]["result"],
        "jev_mrr": cs["jev_mrr"],
        "bm25_mrr": cs["bm25_mrr"],
        "gate4": gates["gates"]["4_construct_validity"]["result"],
        "gate6": gates["gates"]["6_name_meta_ablation"]["result"],
        "usd": cost["total"]["usd"],
        "p50_ms": timing.get("total", {}).get("p50_ms"),
    }, indent=2))


if __name__ == "__main__":
    main()
