# Figure captions — cuad-jev-2026-09-20

Written for a reader who has the Overview glossary in hand. Uncertainty is a **standard error** (s.e.); binomial s.e. = √[*p*(1−*p*)/*n*] for rates. Existing figure files are unchanged; these captions are the prose that sits under them.

1. **inversion_rates** — Share of pairwise Choice pairs on which the judge’s averaged winner was the distractor, not the human-marked span (**inversion**). Left: Stratum A, the 40 certain cross-contract pairs. Right: Stratum B, the 200 same-contract Best Match 25 hard negatives. Whiskers are binomial standard errors. The dashed line is the Gate 1 pass threshold (0.05). Stratum A inversion is 0.000 (s.e. 0.000); Stratum B is 0.320 (s.e. 0.033). Height is a rate, not a dollar or a score.

2. **reliability_stratum_b** — Reliability (calibration) diagram for Stratum B predicted *p*(gold), n=200. Each point is a ten-point-wide probability bin; marker area is proportional to the number of pairs in the bin. Horizontal: mean predicted *p*(gold) in the bin. Vertical: share of pairs in that bin whose discrete winner was the gold span (1 minus inversion). The dashed diagonal is a perfect match of those two axes. The number printed on the figure is the bin-wise expected calibration error against that discrete-correctness axis (0.109 in `results/diagnostics.json`). Gate 5’s table uses a different convention — gold is treated as the correct side on every pair, the same *y* = 1 convention as the Brier score — and reports expected calibration error 0.324. We do not fit a temperature after the fact.

3. **gold_vs_neg_scores** — Gate 4 construct-validity contrast: mean expected Score on human-marked Atticus spans versus Best Match 25 hard-negative paragraphs, under the same category question. Levels map irrelevant = 0 … highly relevant = 3. Means are shown with standard errors of the mean. Gold mean 2.685 (s.e. 0.062, n=100); negative mean 0.555 (s.e. 0.027, n=882); gap 2.130 (s.e. 0.067). If those two means could not be told apart, the Score axis would not be measuring category relevance.

4. **mrr_recall_vs_baselines** — Left: **mean reciprocal rank** of the gold paragraph (average of 1/rank; 1 = gold always first) under Jev expected Score, Best Match 25, and uniform chance among the scored candidates (n=100 queries), with standard errors. Right: **recall at 1, 3, and 5** — the share of queries with gold in the top *k* — for Jev and Best Match 25 (± s.e.) against chance *k*/10. Best Match 25 uses pre-injection ranks: 28 of 100 queries had no gold in the keyword top 10, and those queries contribute 0 to keyword recall at 1/3/5.

5. **mrr_vs_bm25** — Standalone mean-reciprocal-rank panel (same estimates as panel 4, left). Jev 0.917 (s.e. 0.021) versus Best Match 25 0.469 (s.e. 0.041) versus chance 0.298 (s.e. 0.002).

6. **recall_at_k** — Standalone recall-at-*k* panel for Jev versus Best Match 25 (same estimates as panel 4, right). Jev 0.86 / 0.97 / 0.99 versus keyword 0.35 / 0.51 / 0.57 at *k* = 1 / 3 / 5.

7. **gold_rank_hist_cdf** — Left: histogram of the rank of the gold paragraph under Jev Score versus Best Match 25 (1 = highest). Right: empirical cumulative distribution of those ranks — the share of queries whose gold rank is at most the horizontal value. Mass near rank 1 under Jev is the ranking result behind mean reciprocal rank 0.917. Best Match 25 has a longer right tail, including the 28 queries where gold sat outside the keyword top 10.

8. **latency_by_call_type** — Distribution of end-to-end API latency in milliseconds for Choice versus Score calls. Left: overlapping histograms; right: boxplots with extreme outliers suppressed. Overall median (50th percentile) latency is 182 milliseconds; mean 191.1 milliseconds; 95th percentile 258 milliseconds (concurrency 6).

9. **cost_by_stratum** — Dollar cost by call slice at Jev pricing of $0.042 per million input tokens (output free). Slices: Choice on Stratum A stripped ($0.002055), Choice on Stratum A with names in ($0.002094), Choice on Stratum B stripped ($0.012229), Score on candidates ($0.026772). Total run cost is $0.043149 over 1,542 calls.

10. **token_usage_by_stratum** — Input and output token counts by the same slices as the cost panel. Output is not billed. Input volume is dominated by 637,421 tokens on the 982 candidate Score calls (1,027,363 input tokens in total).

11. **cost_latency** — Legacy dual panel: US dollars by slice and median latency with a whisker to the 95th percentile. Prefer panels 8–9 when reading the current writeup.

12. **category_diagnostics** — Left: Stratum B inversion rates by Atticus category (± binomial s.e.; categories with at least 3 pairs). Right: mean Score(gold) − Score(negatives) by category (± s.e. across queries), a category-level construct-validity contrast. Rare categories are noisy; a single bar is not a finding.

13. **corpus_diagnostics** — Corpus shape, not a model result: paragraph character-length distribution; spans per contract; the fifteen most frequent of 41 Atticus categories among 13,823 human marks. Underlying counts: 510 contracts; 21,598 paragraphs; 13,823 spans.

14. **p_gold_distribution** — Histograms of Choice *p*(gold) for Stratum A versus Stratum B (party names and dates stripped). Vertical dashes mark stratum means (0.976 and 0.676). The leftward shift from A to B is the harder same-contract discrimination setting under Best Match 25 hard negatives.

15. **agreement_ablation** — Left: order-flip rates (the two presentation orders disagree on the discrete winner) for Strata A and B (± binomial s.e.). A: 0.000 (n=40). B: 0.075 (n=200). Right: Stratum A inversion under stripped text versus names-and-dates-in text (Gate 6); change in inversion = 0.000.
