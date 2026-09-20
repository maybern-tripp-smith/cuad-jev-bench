#!/usr/bin/env python3
"""Publication figures for cuad-jev-bench."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures"
DOCFIG = ROOT / "docs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
DOCFIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 140,
})


def save(fig, name: str) -> None:
    for d in (FIG, DOCFIG):
        fig.savefig(d / f"{name}.png", bbox_inches="tight")
        fig.savefig(d / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    gates = json.loads((ROOT / "results" / "gates.json").read_text())
    cost = json.loads((ROOT / "results" / "cost.json").read_text())
    timing = json.loads((ROOT / "results" / "timing.json").read_text())
    acc = json.loads((ROOT / "results" / "accuracy_summary.json").read_text())

    # 1) Inversion bars A vs B
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    strata = ["A (certain)", "B (labeled)"]
    inv = [
        gates["gates"]["1_easy_pair_inversion"]["metric"],
        gates["gates"]["2_labeled_pair_inversion_brier"]["inversion"],
    ]
    ste = [
        gates["gates"]["1_easy_pair_inversion"]["ste"] or 0,
        gates["gates"]["2_labeled_pair_inversion_brier"]["inversion_ste"] or 0,
    ]
    bars = ax.bar(strata, inv, yerr=ste, color=["#2c7bb6", "#d7191c"], capsize=4, alpha=0.85)
    ax.axhline(0.05, color="gray", ls="--", lw=1, label="Gate 1 line (0.05)")
    ax.set_ylabel("Inversion rate")
    ax.set_ylim(0, max(0.45, max(inv) + max(ste) + 0.05))
    ax.set_title("Pairwise Choice inversion by stratum")
    ax.legend(frameon=False)
    save(fig, "inversion_rates")

    # 2) MRR vs BM25 vs chance
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    labels = ["Jev Score", "BM25", "Chance"]
    means = [
        acc["candidate"]["mrr_jev"]["mean"],
        acc["candidate"]["mrr_bm25"]["mean"],
        acc["candidate"]["mrr_chance"]["mean"],
    ]
    stes = [
        acc["candidate"]["mrr_jev"]["ste"],
        acc["candidate"]["mrr_bm25"]["ste"],
        acc["candidate"]["mrr_chance"]["ste"],
    ]
    ax.bar(labels, means, yerr=stes, color=["#1a9850", "#91bfdb", "#cccccc"], capsize=4)
    ax.set_ylabel("MRR")
    ax.set_ylim(0, 1.05)
    ax.set_title("Candidate ranking: gold MRR (n_q=100)")
    save(fig, "mrr_vs_bm25")

    # 3) Recall@k
    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    ks = [1, 3, 5]
    jev_r = [acc["candidate"]["recall_jev"][f"@{k}"]["mean"] for k in ks]
    bm_r = [acc["candidate"]["recall_bm25"][f"@{k}"]["mean"] for k in ks]
    x = np.arange(len(ks))
    w = 0.35
    ax.bar(x - w / 2, jev_r, w, label="Jev Score", color="#1a9850")
    ax.bar(x + w / 2, bm_r, w, label="BM25", color="#91bfdb")
    ax.set_xticks(x)
    ax.set_xticklabels([f"R@{k}" for k in ks])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Recall")
    ax.set_title("Recall@k of gold paragraph in top-k")
    ax.legend(frameon=False)
    save(fig, "recall_at_k")

    # 4) Gold vs neg Score means
    fig, ax = plt.subplots(figsize=(5.0, 3.8))
    g = acc["candidate"]["mean_score_gold"]
    n = acc["candidate"]["mean_score_neg"]
    ax.bar(
        ["Gold spans", "BM25 hard-negs"],
        [g["mean"], n["mean"]],
        yerr=[g["ste"], n["ste"]],
        color=["#1a9850", "#fc8d59"],
        capsize=4,
    )
    ax.set_ylabel("Expected Score (0=irrelevant … 3=highly)")
    ax.set_title("Construct validity: Score on gold vs hard-negs")
    ax.set_ylim(0, 3.2)
    save(fig, "gold_vs_neg_scores")

    # 5) Cost / latency
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.6))
    by = cost["by_stratum"]
    keys = sorted(by.keys())
    axes[0].barh(keys, [by[k]["usd"] for k in keys], color="#7570b3")
    axes[0].set_xlabel("USD")
    axes[0].set_title(f"Cost by slice (total ${cost['total']['usd']:.4f})")
    tb = timing.get("by_stratum", {})
    tkeys = sorted(tb.keys())
    axes[1].barh(
        tkeys,
        [tb[k]["p50_ms"] for k in tkeys],
        xerr=[tb[k]["p95_ms"] - tb[k]["p50_ms"] for k in tkeys],
        color="#1b9e77",
        capsize=3,
    )
    axes[1].set_xlabel("Latency ms (p50; whisker to p95)")
    axes[1].set_title(f"Latency (overall p50={timing['total']['p50_ms']:.0f} ms)")
    fig.tight_layout()
    save(fig, "cost_latency")

    captions = """# Figure captions — cuad-jev-2026-09-20

1. **inversion_rates** — Choice inversion rates (both orders averaged) for Stratum A
   (rule-built certain pairs) and Stratum B (BM25 hard-negatives). Error bars: bootstrap STE.
   Dashed line: Gate 1 pass threshold (0.05).

2. **mrr_vs_bm25** — Mean reciprocal rank of the gold paragraph under Jev expected Score,
   BM25 baseline, and uniform chance among top-10 candidates (n_q=100). STE via bootstrap.

3. **recall_at_k** — Recall@1/@3/@5 for gold paragraph under Jev Score vs BM25.

4. **gold_vs_neg_scores** — Mean expected Score on gold CUAD spans vs BM25 hard-negative
   paragraphs (Gate 4 construct validity). Levels: irrelevant=0 … highly relevant=3.

5. **cost_latency** — USD by call slice (Jev $0.042/MTok input, output free) and p50 latency
   with whisker to p95.
"""
    (FIG / "CAPTIONS.md").write_text(captions)
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
