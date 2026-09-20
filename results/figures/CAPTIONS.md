# Figure captions — cuad-jev-2026-09-20

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
