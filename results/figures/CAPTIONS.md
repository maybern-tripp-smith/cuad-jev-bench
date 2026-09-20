# Figure captions — cuad-jev-2026-09-20

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
