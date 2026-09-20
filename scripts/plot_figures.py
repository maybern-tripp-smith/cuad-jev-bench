#!/usr/bin/env python3
"""Publication figures + diagnostics for cuad-jev-bench (economist register)."""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures"
DOCFIG = ROOT / "docs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
DOCFIG.mkdir(parents=True, exist_ok=True)

SEED = 20260920
RNG = np.random.default_rng(SEED)

plt.rcParams.update(
    {
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 140,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
    }
)


def save(fig, name: str) -> None:
    for d in (FIG, DOCFIG):
        fig.savefig(d / f"{name}.png", bbox_inches="tight")
        fig.savefig(d / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def binomial_se(p: float, n: int) -> float:
    if n <= 0:
        return float("nan")
    return float(math.sqrt(max(p * (1.0 - p), 0.0) / n))


def mean_se(xs: list[float] | np.ndarray) -> tuple[float, float, int]:
    arr = np.asarray(list(xs), dtype=float)
    n = int(arr.size)
    if n == 0:
        return float("nan"), float("nan"), 0
    m = float(arr.mean())
    se = float(arr.std(ddof=1) / math.sqrt(n)) if n > 1 else 0.0
    return m, se, n


def ece_reliability(p: np.ndarray, y: np.ndarray, n_bins: int = 10) -> tuple[float, list[dict]]:
    """Equal-width ECE on [0,1]; returns ECE and bin table."""
    bins = []
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(p)
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        if i == n_bins - 1:
            mask = (p >= lo) & (p <= hi)
        else:
            mask = (p >= lo) & (p < hi)
        if not np.any(mask):
            bins.append(
                {
                    "bin": i,
                    "lo": float(lo),
                    "hi": float(hi),
                    "n": 0,
                    "conf_mean": float("nan"),
                    "acc": float("nan"),
                }
            )
            continue
        conf = float(p[mask].mean())
        acc = float(y[mask].mean())
        weight = float(mask.sum()) / n
        ece += weight * abs(acc - conf)
        bins.append(
            {
                "bin": i,
                "lo": float(lo),
                "hi": float(hi),
                "n": int(mask.sum()),
                "conf_mean": conf,
                "acc": acc,
            }
        )
    return float(ece), bins


def load_json(name: str):
    return json.loads((ROOT / "results" / name).read_text())


def load_pairs() -> list[dict]:
    rows = []
    with open(ROOT / "results" / "pair_judgments.jsonl") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def load_candidate_rows() -> list[dict]:
    with open(ROOT / "results" / "candidate_scores.csv") as f:
        return list(csv.DictReader(f))


def load_answers() -> list[dict]:
    rows = []
    with open(ROOT / "runs" / "jev" / "answers.jsonl") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def plot_inversion(gates: dict, diagnostics: dict) -> None:
    fig, ax = plt.subplots(figsize=(5.6, 3.9))
    strata = ["A (certain)", "B (BM25 hard-neg)"]
    inv = [
        gates["gates"]["1_easy_pair_inversion"]["metric"],
        gates["gates"]["2_labeled_pair_inversion_brier"]["inversion"],
    ]
    n = [
        gates["gates"]["1_easy_pair_inversion"]["n"],
        gates["gates"]["2_labeled_pair_inversion_brier"]["n"],
    ]
    se = [binomial_se(inv[0], n[0]), binomial_se(inv[1], n[1])]
    ax.bar(strata, inv, yerr=se, color=["#2c7bb6", "#d7191c"], capsize=4, alpha=0.88, width=0.55)
    ax.axhline(0.05, color="gray", ls="--", lw=1, label="Gate 1 line (0.05)")
    for i, (v, s, ni) in enumerate(zip(inv, se, n)):
        ax.text(i, v + s + 0.015, f"{v:.3f}\n(s.e. {s:.3f}, n={ni})", ha="center", va="bottom", fontsize=8)
    ax.set_ylabel("Inversion rate")
    ax.set_ylim(0, max(0.50, max(inv) + max(se) + 0.12))
    ax.set_title("Choice inversion by stratum (± binomial s.e.)")
    ax.legend(frameon=False, loc="upper left")
    save(fig, "inversion_rates")
    diagnostics["inversion_by_stratum"] = [
        {"stratum": "A", "inversion": inv[0], "se_binomial": se[0], "n": n[0]},
        {"stratum": "B", "inversion": inv[1], "se_binomial": se[1], "n": n[1]},
    ]


def plot_reliability(pairs: list[dict], diagnostics: dict) -> None:
    b = [p for p in pairs if p["stratum"] == "B" and p.get("mode") == "stripped"]
    # one row per pair_id already averaged in pair_judgments
    p = np.array([float(x["p_gold"]) for x in b], dtype=float)
    # binary correctness: not inverted
    y = np.array([0.0 if x["inverted"] else 1.0 for x in b], dtype=float)
    ece, bins = ece_reliability(p, y, n_bins=10)
    fig, ax = plt.subplots(figsize=(5.4, 5.0))
    confs = [b["conf_mean"] for b in bins if b["n"] > 0]
    accs = [b["acc"] for b in bins if b["n"] > 0]
    ns = [b["n"] for b in bins if b["n"] > 0]
    sizes = [40 + 4 * n for n in ns]
    ax.plot([0, 1], [0, 1], ls="--", color="gray", lw=1, label="Perfect calibration")
    ax.scatter(confs, accs, s=sizes, c="#2c7bb6", alpha=0.85, zorder=3, label="Bin (size ∝ n)")
    # connect in order of conf
    order = np.argsort(confs)
    ax.plot(np.array(confs)[order], np.array(accs)[order], color="#2c7bb6", lw=1, alpha=0.5)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Mean predicted p(gold) in bin")
    ax.set_ylabel("Empirical share correct (1 − inversion)")
    ax.set_title(f"Reliability diagram, Stratum B (ECE = {ece:.3f}, n={len(b)})")
    ax.legend(frameon=False, loc="upper left")
    ax.text(0.98, 0.05, f"ECE = {ece:.3f}", ha="right", va="bottom", fontsize=10, transform=ax.transAxes)
    save(fig, "reliability_stratum_b")
    diagnostics["calibration_stratum_b"] = {
        "ece": ece,
        "n": len(b),
        "n_bins": 10,
        "bins": bins,
        "mean_p_gold": float(p.mean()),
        "mean_correct": float(y.mean()),
    }


def plot_gold_vs_neg(acc: dict, diagnostics: dict) -> None:
    fig, ax = plt.subplots(figsize=(5.2, 3.9))
    g = acc["candidate"]["mean_score_gold"]
    n = acc["candidate"]["mean_score_neg"]
    means = [g["mean"], n["mean"]]
    ses = [g["ste"], n["ste"]]
    ax.bar(
        ["Gold spans", "BM25 hard-negs"],
        means,
        yerr=ses,
        color=["#1a9850", "#fc8d59"],
        capsize=4,
        width=0.55,
    )
    ax.set_ylabel("Expected Score (0=irrelevant … 3=highly)")
    ax.set_title("Gate 4 construct validity: Score means ± s.e.")
    ax.set_ylim(0, 3.25)
    gap = means[0] - means[1]
    gap_se = math.sqrt(ses[0] ** 2 + ses[1] ** 2)
    ax.text(
        0.5,
        2.95,
        f"gap = {gap:.3f} (s.e. {gap_se:.3f})",
        ha="center",
        fontsize=9,
        transform=ax.get_xaxis_transform() if False else ax.transData,
    )
    save(fig, "gold_vs_neg_scores")
    diagnostics["gate4_score_means"] = {
        "gold": g,
        "hard_neg": n,
        "gap_mean": gap,
        "gap_se": gap_se,
    }


def plot_mrr_recall(acc: dict, diagnostics: dict) -> None:
    # Combined figure: MRR + Recall@k
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.9))
    labels = ["Jev Score", "BM25", "Chance"]
    means = [
        acc["candidate"]["mrr_jev"]["mean"],
        acc["candidate"]["mrr_bm25"]["mean"],
        acc["candidate"]["mrr_chance"]["mean"],
    ]
    ses = [
        acc["candidate"]["mrr_jev"]["ste"],
        acc["candidate"]["mrr_bm25"]["ste"],
        acc["candidate"]["mrr_chance"]["ste"],
    ]
    axes[0].bar(labels, means, yerr=ses, color=["#1a9850", "#91bfdb", "#cccccc"], capsize=4)
    axes[0].set_ylabel("MRR")
    axes[0].set_ylim(0, 1.08)
    axes[0].set_title("Gold MRR (n_q=100) ± s.e.")

    ks = [1, 3, 5]
    jev_r = [acc["candidate"]["recall_jev"][f"@{k}"]["mean"] for k in ks]
    bm_r = [acc["candidate"]["recall_bm25"][f"@{k}"]["mean"] for k in ks]
    jev_se = [acc["candidate"]["recall_jev"][f"@{k}"]["ste"] for k in ks]
    bm_se = [acc["candidate"]["recall_bm25"][f"@{k}"]["ste"] for k in ks]
    # chance recall@k among 10: k/10
    chance_r = [k / 10.0 for k in ks]
    x = np.arange(len(ks))
    w = 0.25
    axes[1].bar(x - w, jev_r, w, yerr=jev_se, label="Jev Score", color="#1a9850", capsize=3)
    axes[1].bar(x, bm_r, w, yerr=bm_se, label="BM25", color="#91bfdb", capsize=3)
    axes[1].bar(x + w, chance_r, w, label="Chance (k/10)", color="#cccccc")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([f"R@{k}" for k in ks])
    axes[1].set_ylim(0, 1.08)
    axes[1].set_ylabel("Recall")
    axes[1].set_title("Recall@k ± s.e.")
    axes[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    save(fig, "mrr_recall_vs_baselines")

    # Also keep legacy separate names for continuity
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    ax.bar(labels, means, yerr=ses, color=["#1a9850", "#91bfdb", "#cccccc"], capsize=4)
    ax.set_ylabel("MRR")
    ax.set_ylim(0, 1.08)
    ax.set_title("Candidate ranking: gold MRR (n_q=100)")
    save(fig, "mrr_vs_bm25")

    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    ax.bar(x - w / 2, jev_r, w, yerr=jev_se, label="Jev Score", color="#1a9850", capsize=3)
    ax.bar(x + w / 2, bm_r, w, yerr=bm_se, label="BM25", color="#91bfdb", capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels([f"R@{k}" for k in ks])
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Recall")
    ax.set_title("Recall@k of gold paragraph in top-k")
    ax.legend(frameon=False)
    save(fig, "recall_at_k")

    diagnostics["ranking"] = {
        "mrr": {"jev": acc["candidate"]["mrr_jev"], "bm25": acc["candidate"]["mrr_bm25"], "chance": acc["candidate"]["mrr_chance"]},
        "recall_jev": acc["candidate"]["recall_jev"],
        "recall_bm25": acc["candidate"]["recall_bm25"],
        "chance_recall_at_k": {f"@{k}": k / 10.0 for k in ks},
    }


def plot_gold_rank_hist_cdf(cand: list[dict], diagnostics: dict) -> None:
    # first gold rank under Jev; BM25 first-gold from column (same per query)
    by_q: dict[str, dict] = {}
    for row in cand:
        q = row["query_id"]
        if q not in by_q:
            by_q[q] = {
                "bm25": int(float(row["bm25_rank_first_gold"])) if row.get("bm25_rank_first_gold") else None,
                "jev_ranks": [],
            }
        if row["is_gold"] in ("True", "true", "1"):
            by_q[q]["jev_ranks"].append(int(float(row["rank_jev"])))
    jev_ranks = [min(v["jev_ranks"]) for v in by_q.values() if v["jev_ranks"]]
    bm_ranks = [v["bm25"] for v in by_q.values() if v["bm25"] is not None]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.9))
    bins = np.arange(0.5, 11.5, 1.0)
    axes[0].hist(jev_ranks, bins=bins, alpha=0.75, color="#1a9850", label="Jev Score", edgecolor="white")
    axes[0].hist(bm_ranks, bins=bins, alpha=0.55, color="#91bfdb", label="BM25", edgecolor="white")
    axes[0].set_xlabel("Rank of gold paragraph (1 = best)")
    axes[0].set_ylabel("Number of queries")
    axes[0].set_title("Gold-rank histogram (n_q=100)")
    axes[0].legend(frameon=False)
    axes[0].set_xticks(range(1, 11))

    for ranks, color, label in (
        (jev_ranks, "#1a9850", "Jev Score"),
        (bm_ranks, "#2c7bb6", "BM25"),
    ):
        xs = np.sort(np.asarray(ranks, dtype=float))
        ys = np.arange(1, len(xs) + 1) / len(xs)
        axes[1].step(xs, ys, where="post", color=color, label=label, lw=1.8)
    axes[1].set_xlabel("Rank of gold paragraph")
    axes[1].set_ylabel("Empirical CDF")
    axes[1].set_xlim(0.5, 10.5)
    axes[1].set_ylim(0, 1.02)
    axes[1].set_title("Gold-rank CDF")
    axes[1].legend(frameon=False, loc="lower right")
    fig.tight_layout()
    save(fig, "gold_rank_hist_cdf")
    diagnostics["gold_ranks"] = {
        "jev_mean": float(np.mean(jev_ranks)),
        "jev_se": float(np.std(jev_ranks, ddof=1) / math.sqrt(len(jev_ranks))),
        "bm25_mean": float(np.mean(bm_ranks)),
        "bm25_se": float(np.std(bm_ranks, ddof=1) / math.sqrt(len(bm_ranks))),
        "jev_share_rank1": float(np.mean(np.asarray(jev_ranks) == 1)),
        "bm25_share_rank1": float(np.mean(np.asarray(bm_ranks) == 1)),
        "n": len(jev_ranks),
    }


def plot_latency(answers: list[dict], diagnostics: dict) -> None:
    choice = [a["latency_ms"] for a in answers if a.get("kind") == "choice" and a.get("latency_ms") is not None]
    score = [a["latency_ms"] for a in answers if a.get("kind") == "score" and a.get("latency_ms") is not None]
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.9))
    axes[0].hist(choice, bins=30, color="#7570b3", alpha=0.85, edgecolor="white", label="Choice")
    axes[0].hist(score, bins=30, color="#1b9e77", alpha=0.55, edgecolor="white", label="Score")
    axes[0].set_xlabel("Latency (ms)")
    axes[0].set_ylabel("Calls")
    axes[0].set_title("Latency distribution by call type")
    axes[0].legend(frameon=False)

    data = [choice, score]
    bp = axes[1].boxplot(data, tick_labels=["Choice", "Score"], patch_artist=True, showfliers=False)
    for patch, c in zip(bp["boxes"], ["#7570b3", "#1b9e77"]):
        patch.set_facecolor(c)
        patch.set_alpha(0.7)
    axes[1].set_ylabel("Latency (ms)")
    axes[1].set_title("Latency boxplot (outliers suppressed)")
    fig.tight_layout()
    save(fig, "latency_by_call_type")

    def summ(xs):
        arr = np.asarray(xs, dtype=float)
        return {
            "n": int(arr.size),
            "mean": float(arr.mean()),
            "se": float(arr.std(ddof=1) / math.sqrt(arr.size)),
            "p50": float(np.percentile(arr, 50)),
            "p95": float(np.percentile(arr, 95)),
        }

    diagnostics["latency_by_call_type"] = {"choice": summ(choice), "score": summ(score)}


def plot_cost_tokens(cost: dict, diagnostics: dict) -> None:
    by = cost["by_stratum"]
    # map to friendly labels / stratum groups
    order = [
        ("choice_stripped_A", "Choice A\n(stripped)"),
        ("choice_names_in_A", "Choice A\n(names-in)"),
        ("choice_stripped_B", "Choice B\n(stripped)"),
        ("score_candidates", "Score\ncandidates"),
    ]
    keys = [k for k, _ in order if k in by]
    labels = [lab for k, lab in order if k in by]
    usd = [by[k]["usd"] for k in keys]
    toks = [by[k]["input_tokens"] for k in keys]
    out_toks = [by[k]["output_tokens"] for k in keys]

    fig, ax = plt.subplots(figsize=(6.2, 3.9))
    x = np.arange(len(keys))
    ax.bar(x, usd, color=["#2c7bb6", "#74add1", "#d7191c", "#1a9850"], alpha=0.88)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("USD (input @ $0.042/MTok)")
    ax.set_title(f"Cost by slice (total ${cost['total']['usd']:.5f})")
    for i, v in enumerate(usd):
        ax.text(i, v + 0.0004, f"${v:.4f}", ha="center", fontsize=8)
    save(fig, "cost_by_stratum")

    fig, ax = plt.subplots(figsize=(6.2, 3.9))
    w = 0.38
    ax.bar(x - w / 2, toks, w, label="Input tokens", color="#4575b4")
    ax.bar(x + w / 2, out_toks, w, label="Output tokens", color="#fdae61")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Tokens")
    ax.set_title("Token usage by slice")
    ax.legend(frameon=False)
    save(fig, "token_usage_by_stratum")

    # legacy dual panel
    timing = load_json("timing.json")
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.6))
    tkeys = sorted(by.keys())
    axes[0].barh(tkeys, [by[k]["usd"] for k in tkeys], color="#7570b3")
    axes[0].set_xlabel("USD")
    axes[0].set_title(f"Cost by slice (total ${cost['total']['usd']:.4f})")
    tb = timing.get("by_stratum", {})
    tk = sorted(tb.keys())
    axes[1].barh(
        tk,
        [tb[k]["p50_ms"] for k in tk],
        xerr=[tb[k]["p95_ms"] - tb[k]["p50_ms"] for k in tk],
        color="#1b9e77",
        capsize=3,
    )
    axes[1].set_xlabel("Latency ms (p50; whisker to p95)")
    axes[1].set_title(f"Latency (overall p50={timing['total']['p50_ms']:.0f} ms)")
    fig.tight_layout()
    save(fig, "cost_latency")

    diagnostics["cost_by_slice"] = by
    diagnostics["cost_total"] = cost["total"]
    diagnostics["token_usage_by_slice"] = {
        k: {"input_tokens": by[k]["input_tokens"], "output_tokens": by[k]["output_tokens"]} for k in by
    }


def plot_category_diagnostics(pairs: list[dict], cand: list[dict], diagnostics: dict) -> None:
    # Stratum B inversion by category
    b = [p for p in pairs if p["stratum"] == "B" and p.get("mode") == "stripped"]
    by_cat: dict[str, list[int]] = defaultdict(list)
    for p in b:
        by_cat[p["category"]].append(1 if p["inverted"] else 0)
    cat_stats = []
    for cat, ys in by_cat.items():
        n = len(ys)
        inv = sum(ys) / n
        cat_stats.append({"category": cat, "n": n, "inversion": inv, "se": binomial_se(inv, n)})
    cat_stats.sort(key=lambda d: (d["inversion"], d["n"]), reverse=True)

    # Score gap by category from candidate scores
    gap_rows = []
    by_qc: dict[tuple[str, str], dict] = defaultdict(lambda: {"gold": [], "neg": []})
    for row in cand:
        key = (row["query_id"], row["category"])
        sc = float(row["score"])
        if row["is_gold"] in ("True", "true", "1"):
            by_qc[key]["gold"].append(sc)
        else:
            by_qc[key]["neg"].append(sc)
    by_cat_gap: dict[str, list[float]] = defaultdict(list)
    for (q, cat), v in by_qc.items():
        if v["gold"] and v["neg"]:
            by_cat_gap[cat].append(float(np.mean(v["gold"]) - np.mean(v["neg"])))
    gap_stats = []
    for cat, gaps in by_cat_gap.items():
        m, se, n = mean_se(gaps)
        gap_stats.append({"category": cat, "n_queries": n, "mean_score_gap": m, "se": se})
    gap_stats.sort(key=lambda d: d["mean_score_gap"], reverse=True)

    # Plot: top/bottom inversion categories with n>=3
    usable = [c for c in cat_stats if c["n"] >= 3]
    top = usable[:8]
    bot = usable[-8:] if len(usable) > 8 else usable
    # unique ordered for display: highest inv then lowest
    show = []
    seen = set()
    for c in top + list(reversed(bot)):
        if c["category"] not in seen:
            show.append(c)
            seen.add(c["category"])
    show = show[:12]
    show = list(reversed(show))  # highest at top in barh

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 5.2))
    cats = [c["category"] for c in show]
    invs = [c["inversion"] for c in show]
    ses = [c["se"] for c in show]
    axes[0].barh(cats, invs, xerr=ses, color="#d7191c", alpha=0.8, capsize=3)
    axes[0].set_xlabel("Inversion rate ± binomial s.e.")
    axes[0].set_title("Stratum B inversion by CUAD category")
    axes[0].axvline(0.32, color="gray", ls="--", lw=1, label="Overall B (0.32)")
    axes[0].legend(frameon=False, fontsize=8)

    # score gaps: top 8 and bottom 8
    gshow = list(reversed(gap_stats[:8] + gap_stats[-8:][::-1]))
    # dedupe
    g2 = []
    seen = set()
    for g in gap_stats[:8] + list(reversed(gap_stats[-8:])):
        if g["category"] not in seen:
            g2.append(g)
            seen.add(g["category"])
    g2 = list(reversed(g2[:12]))
    axes[1].barh(
        [g["category"] for g in g2],
        [g["mean_score_gap"] for g in g2],
        xerr=[g["se"] for g in g2],
        color="#1a9850",
        alpha=0.8,
        capsize=3,
    )
    axes[1].set_xlabel("Mean Score(gold) − Score(neg) ± s.e.")
    axes[1].set_title("Construct-validity gap by category")
    fig.tight_layout()
    save(fig, "category_diagnostics")

    diagnostics["category_inversion_B"] = cat_stats
    diagnostics["category_score_gap"] = gap_stats


def plot_corpus(data_stats: dict, diagnostics: dict) -> None:
    # paragraph lengths from clean file (full)
    plens = []
    with open(ROOT / "data" / "clean" / "paragraphs.jsonl") as f:
        for line in f:
            o = json.loads(line)
            plens.append(int(o.get("n_chars") or len(o.get("text") or "")))
    spans_per_contract: Counter = Counter()
    with open(ROOT / "data" / "labels" / "spans.jsonl") as f:
        for line in f:
            o = json.loads(line)
            cid = o.get("contract_id") or o.get("title") or o.get("doc_id")
            if cid is None and "id" in o:
                cid = str(o["id"]).split("__")[0]
            if cid is None:
                # try common patterns
                for k in ("contract", "document", "file"):
                    if k in o:
                        cid = o[k]
                        break
            if cid is None:
                continue
            spans_per_contract[cid] += 1

    # if empty, fall back to data_stats only for category freq
    fig, axes = plt.subplots(1, 3, figsize=(12.0, 3.8))
    axes[0].hist(plens, bins=40, color="#4575b4", edgecolor="white", alpha=0.85)
    axes[0].axvline(np.median(plens), color="#d7191c", ls="--", lw=1, label=f"p50={int(np.median(plens))}")
    axes[0].set_xlabel("Paragraph length (chars)")
    axes[0].set_ylabel("Count")
    axes[0].set_title("Paragraph length distribution")
    axes[0].legend(frameon=False, fontsize=8)

    if spans_per_contract:
        vals = list(spans_per_contract.values())
        axes[1].hist(vals, bins=30, color="#1a9850", edgecolor="white", alpha=0.85)
        axes[1].set_xlabel("Spans per contract")
        axes[1].set_ylabel("Contracts")
        axes[1].set_title(f"Spans per contract (mean={np.mean(vals):.1f})")
    else:
        axes[1].text(0.5, 0.5, "spans-per-contract\nunavailable", ha="center", va="center", transform=axes[1].transAxes)
        axes[1].set_axis_off()

    cats = data_stats.get("category_counts", {})
    top = sorted(cats.items(), key=lambda kv: kv[1], reverse=True)[:15]
    axes[2].barh([c for c, _ in reversed(top)], [n for _, n in reversed(top)], color="#fdae61")
    axes[2].set_xlabel("Annotated spans")
    axes[2].set_title("Top-15 CUAD category frequency")
    fig.tight_layout()
    save(fig, "corpus_diagnostics")

    diagnostics["corpus"] = {
        "n_contracts": data_stats.get("n_contracts"),
        "n_paragraphs": data_stats.get("n_paragraphs"),
        "n_spans": data_stats.get("n_spans"),
        "paragraph_length_chars": data_stats.get("paragraph_length_chars"),
        "spans_per_contract": {
            "n_contracts_with_spans": len(spans_per_contract),
            "mean": float(np.mean(list(spans_per_contract.values()))) if spans_per_contract else None,
            "p50": float(np.median(list(spans_per_contract.values()))) if spans_per_contract else None,
        },
        "category_counts_top15": dict(top),
    }


def plot_p_gold_dist(pairs: list[dict], diagnostics: dict) -> None:
    a = [float(p["p_gold"]) for p in pairs if p["stratum"] == "A" and p.get("mode") == "stripped"]
    b = [float(p["p_gold"]) for p in pairs if p["stratum"] == "B" and p.get("mode") == "stripped"]
    fig, ax = plt.subplots(figsize=(5.8, 3.9))
    bins = np.linspace(0, 1, 21)
    ax.hist(a, bins=bins, alpha=0.7, color="#2c7bb6", label=f"A (n={len(a)})", edgecolor="white")
    ax.hist(b, bins=bins, alpha=0.55, color="#d7191c", label=f"B (n={len(b)})", edgecolor="white")
    ax.axvline(np.mean(a), color="#2c7bb6", ls="--", lw=1)
    ax.axvline(np.mean(b), color="#d7191c", ls="--", lw=1)
    ax.set_xlabel("p(gold)")
    ax.set_ylabel("Pairs")
    ax.set_title("Distribution of p(gold): Stratum A vs B")
    ax.legend(frameon=False)
    save(fig, "p_gold_distribution")
    ma, sea, na = mean_se(a)
    mb, seb, nb = mean_se(b)
    diagnostics["p_gold_distribution"] = {
        "A": {"mean": ma, "se": sea, "n": na, "p10": float(np.percentile(a, 10)), "p50": float(np.percentile(a, 50)), "p90": float(np.percentile(a, 90))},
        "B": {"mean": mb, "se": seb, "n": nb, "p10": float(np.percentile(b, 10)), "p50": float(np.percentile(b, 50)), "p90": float(np.percentile(b, 90))},
    }


def plot_agreement(pairs: list[dict], gates: dict, diagnostics: dict) -> None:
    a_s = [p for p in pairs if p["stratum"] == "A" and p.get("mode") == "stripped"]
    a_n = [p for p in pairs if p["stratum"] == "A" and p.get("mode") == "names_in"]
    b_s = [p for p in pairs if p["stratum"] == "B" and p.get("mode") == "stripped"]
    flip_a = float(np.mean([1.0 if p.get("order_flip") else 0.0 for p in a_s])) if a_s else float("nan")
    flip_b = float(np.mean([1.0 if p.get("order_flip") else 0.0 for p in b_s])) if b_s else float("nan")
    inv_s = gates["gates"]["6_name_meta_ablation"]["inversion_stripped"]
    inv_n = gates["gates"]["6_name_meta_ablation"]["inversion_names_in"]
    delta = gates["gates"]["6_name_meta_ablation"]["delta_inversion"]

    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.9))
    axes[0].bar(
        ["A order-flip", "B order-flip"],
        [flip_a, flip_b],
        yerr=[binomial_se(flip_a, len(a_s)), binomial_se(flip_b, len(b_s))],
        color=["#2c7bb6", "#d7191c"],
        capsize=4,
        width=0.55,
    )
    axes[0].set_ylabel("Rate")
    axes[0].set_title("Order-flip rate (± binomial s.e.)")
    axes[0].set_ylim(0, max(0.2, flip_b + 0.08))

    axes[1].bar(
        ["A stripped", "A names-in"],
        [inv_s, inv_n],
        color=["#74add1", "#fdae61"],
        width=0.55,
    )
    axes[1].set_ylabel("Inversion rate")
    axes[1].set_title(f"Name ablation (Δ = {delta:.4f})")
    axes[1].set_ylim(0, 0.12)
    fig.tight_layout()
    save(fig, "agreement_ablation")

    diagnostics["agreement"] = {
        "order_flip_A": {"rate": flip_a, "se": binomial_se(flip_a, len(a_s)), "n": len(a_s)},
        "order_flip_B": {"rate": flip_b, "se": binomial_se(flip_b, len(b_s)), "n": len(b_s)},
        "name_ablation": {
            "inversion_stripped": inv_s,
            "inversion_names_in": inv_n,
            "delta": delta,
            "n": gates["gates"]["6_name_meta_ablation"]["n"],
        },
    }


def write_captions() -> None:
    captions = """# Figure captions — cuad-jev-2026-09-20

Economist-audience captions. Uncertainty is reported as a **standard error** (s.e.); binomial s.e. = √[p(1−p)/n] for rates.

1. **inversion_rates** — Pairwise Choice inversion rates for Stratum A (rule-built certain cross-contract negatives; n=40) and Stratum B (same-contract BM25 hard-negatives; n=200). Error bars are binomial standard errors. The dashed line marks the Gate 1 pass threshold (0.05). Stratum A inversion is 0.000 (s.e. 0.000); Stratum B is 0.320 (s.e. 0.033).

2. **reliability_stratum_b** — Reliability (calibration) diagram for Stratum B predicted p(gold). Points are equal-width probability bins (marker area ∝ bin count). The dashed diagonal is perfect calibration. Expected calibration error (ECE) = 0.324 (n=200), indicating systematic overconfidence relative to binary correctness.

3. **gold_vs_neg_scores** — Gate 4 construct validity: mean expected Score on human gold CUAD spans versus BM25 hard-negative paragraphs under the same category query. Levels map irrelevant=0 … highly relevant=3. Means are shown with standard errors of the mean; the gold−neg gap is approximately 2.13 (s.e. 0.067).

4. **mrr_recall_vs_baselines** — Left: mean reciprocal rank (MRR) of the gold paragraph under Jev expected Score, BM25, and uniform chance among the top-10 candidates (n_q=100), with bootstrap standard errors. Right: Recall@{1,3,5} for Jev and BM25 (± s.e.) against a chance benchmark of k/10.

5. **mrr_vs_bm25** — Standalone MRR panel (same estimates as panel 4, left).

6. **recall_at_k** — Standalone Recall@k panel for Jev versus BM25.

7. **gold_rank_hist_cdf** — Left: histogram of the rank of the gold paragraph under Jev Score versus BM25 (1 = highest). Right: empirical CDFs of those ranks. Mass near rank 1 under Jev indicates recovery of annotated spans above the lexical baseline.

8. **latency_by_call_type** — Distribution of end-to-end API latency (ms) for Choice versus Score calls. Left: overlapping histograms; right: boxplots with extreme outliers suppressed. Overall p50 latency is 182 ms.

9. **cost_by_stratum** — Dollar cost by call slice at Jev pricing of $0.042 per million input tokens (output free). Candidate Score dominates spend; total run cost is approximately $0.043.

10. **token_usage_by_stratum** — Input and output token counts by the same slices as the cost panel.

11. **cost_latency** — Legacy dual panel: USD by slice and p50 latency with whisker to p95.

12. **category_diagnostics** — Left: Stratum B inversion rates by CUAD category (± binomial s.e.; categories with n≥3). Right: mean Score(gold)−Score(neg) by category (± s.e. across queries), a category-level construct-validity contrast.

13. **corpus_diagnostics** — Corpus shape: paragraph character-length distribution; spans per contract; top-15 CUAD category frequencies among human annotations (510 contracts; 21,598 paragraphs; 13,823 spans).

14. **p_gold_distribution** — Histograms of Choice p(gold) for Stratum A versus Stratum B (stripped meta). Vertical dashes mark stratum means. The leftward shift from A to B is consistent with a harder discrimination task under BM25 hard-negatives.

15. **agreement_ablation** — Left: order-flip rates (disagreement across presentation orders) for Strata A and B (± binomial s.e.). Right: Stratum A inversion under stripped versus names-in text (Gate 6); Δ inversion = 0.000.
"""
    (FIG / "CAPTIONS.md").write_text(captions)


def main() -> None:
    gates = load_json("gates.json")
    cost = load_json("cost.json")
    acc = load_json("accuracy_summary.json")
    data_stats = load_json("data_stats.json")
    pairs = load_pairs()
    cand = load_candidate_rows()
    answers = load_answers()

    diagnostics: dict = {
        "run_id": "cuad-jev-2026-09-20",
        "model_resolved": gates.get("model_resolved"),
        "criterion": gates.get("criterion"),
        "uncertainty_notes": {
            "rate_se": "binomial standard error sqrt(p*(1-p)/n)",
            "mean_se": "sample standard deviation / sqrt(n)",
            "gap_se": "sqrt(se_a^2 + se_b^2) for independent means",
            "bootstrap_se_source": "accuracy_summary / gates bootstrap STE fields retained as standard errors",
        },
    }

    plot_inversion(gates, diagnostics)
    plot_reliability(pairs, diagnostics)
    plot_gold_vs_neg(acc, diagnostics)
    plot_mrr_recall(acc, diagnostics)
    plot_gold_rank_hist_cdf(cand, diagnostics)
    plot_latency(answers, diagnostics)
    plot_cost_tokens(cost, diagnostics)
    plot_category_diagnostics(pairs, cand, diagnostics)
    plot_corpus(data_stats, diagnostics)
    plot_p_gold_dist(pairs, diagnostics)
    plot_agreement(pairs, gates, diagnostics)
    write_captions()

    # Attach gate summary for convenience
    diagnostics["gates_summary"] = {
        k: {kk: vv for kk, vv in v.items() if kk != "inverted_ids"} if isinstance(v, dict) else v
        for k, v in gates["gates"].items()
    }
    diagnostics["strata_summary"] = gates.get("strata_summary")

    out = ROOT / "results" / "diagnostics.json"
    out.write_text(json.dumps(diagnostics, indent=2, default=str) + "\n")
    print("figures written to", FIG)
    print("diagnostics written to", out)
    pngs = sorted(DOCFIG.glob("*.png"))
    print(f"docs/figures PNG count: {len(pngs)}")
    for p in pngs:
        print(" ", p.name)


if __name__ == "__main__":
    main()
