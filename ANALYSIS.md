# ANALYSIS — cuad-jev-bench

**run_id:** `cuad-jev-2026-09-20`  
**model:** `jev-1.13.0` (requested `jev-latest`)  
**criterion (exact):** `more relevant to the requested contract category`

## Abstract

We evaluate TypeSafe/Jev on open CUAD contract text under a frozen pairwise and graded-relevance protocol. Labels are human CUAD span annotations only. On 40 rule-built certain pairs (Stratum A), Choice inversion is 0.0000 (STE 0.0000). On 200 BM25 hard-negative pairs (Stratum B), inversion is 0.3200 (STE 0.0324) with Brier 0.2495. For 100 (contract, category) candidate-ranking queries, expected Score yields gold MRR 0.917 (STE 0.021) versus BM25 MRR 0.469 and chance MRR 0.298. Mean Score on gold spans exceeds mean Score on BM25 hard-negatives by 2.130 (STE 0.067). Name/date ablation leaves Stratum A inversion unchanged (Δ=0.0000). Published DeBERTa-xlarge extractive metrics are cited for difficulty context only; this bench does not re-run DeBERTa. Total Jev spend ≈ $0.04315; overall p50 latency 182 ms.

## Contributions

1. A FedLock/fedjev-style open-data Jev bench for **contract-clause relevance** with pre-registered gates, frozen gold, and cost/latency reporting.
2. Design A: certain cross-contract negatives + same-contract BM25 hard-negatives, both orders Choice.
3. Candidate-score lite: BM25 top-10 re-ranked by Jev Score levels, with gold injection logged when needed for measurable rank.
4. Construct-validity contrast (gold vs hard-neg Score means) separate from retrieval baselines.
5. Explicit non-claim on DeBERTa: literature numbers only.

## Methods

### Data

CUAD v1 (`theatticusproject/cuad`), CC BY 4.0. 510 contracts → 21598 paragraph chunks; 13823 human spans across 41 categories. See `DATA.md` and `data/stats/corpus_stats.json`.

### Criterion and interfaces

- **Choice** instructions embed the category name and CUAD “Details” description, then ask which of Text A or Text B is `more relevant to the requested contract category`.
- **Score** levels: `irrelevant / weakly relevant / relevant / highly relevant`. Expected score ∈ [0, 3].
- Main tables use `strip_meta` (party-like corporate names, dates, contact furniture). Gate 6 re-runs Stratum A with raw text.

### Strata

| Stratum | n | Construction |
|---------|--:|--------------|
| A | 40 | Gold span vs paragraph from a contract with no annotation for that category |
| B | 200 | Gold span vs BM25 hard-neg in same contract (seed 20260920) |
| Candidates | 100 queries × ≤10 paras | BM25 top-10; gold injected if absent |

Gold pairs were written to `data/pairs/gold_pairs.jsonl` **before** the first live call (REPORT mtime 17:30:16 EDT; gold mtime 17:32:37 EDT; score start after freeze).

### Gates

Pre-registered in `REPORT.md` before any Jev output. Bootstrap STE (seed 20260920, 1000 resamples) where noted.

## Results

### Gate table

| # | Gate | Result | Detail |
|---|------|--------|--------|
| 1 | Easy-pair inversion | **PASS** | 0.0000 (n=40, STE=0.0000) |
| 2 | Labeled inversion + Brier | report | inv=0.3200 STE=0.0324; Brier=0.2495 STE=0.0257; mean p(gold)=0.6757 |
| 3 | Candidate Score vs BM25 | **PASS_SIGNAL** | Jev MRR=0.917 > BM25=0.469; R@1=0.86 vs 0.35 |
| 4 | Construct validity | **PASS** | mean Score gold=2.685 (STE 0.062) > neg=0.555 (STE 0.027); gap=2.130 |
| 5 | Brier / ECE (B) | report | Brier=0.2495; ECE=0.3243 |
| 6 | Name/meta ablation | **PASS** | Δ inversion=0.0000 |
| 7 | Literature DeBERTa | report | AUPR 47.8, P@80R 44.0, P@90R 17.8 (Hendrycks et al. 2021); not re-run |

### Cost and timing

Total ≈ **$0.04315** over 1542 logged calls (1027363 input tokens @ $0.042/MTok; output free). Overall latency mean 191.1 ms, **p50 182 ms**, p95 258 ms (concurrency 6).

### Interpretation

Stratum A shows that under an easy relevance contrast, Jev Choice does not invert. Stratum B is harder: BM25-selected negatives from the same contract share topical vocabulary, and inversion rises to ~32%—consistent with a difficult discrimination setting rather than a vacuous task. Candidate Score recovers gold paragraphs far above BM25 and chance, and gold spans receive substantially higher expected Scores than hard-negatives (Gate 4), supporting construct validity of the relevance Score axis. Calibration on Stratum B (ECE ≈ 0.32) indicates overconfidence relative to binary gold; we report this without post-hoc temperature fitting. Gate 7’s DeBERTa numbers describe **extractive** difficulty on CUAD; our task is candidate scoring / pairwise relevance, so numerical comparison is narrative only.

## Limitations

- Paragraph chunking is heuristic; gold spans may cross chunk boundaries (we map via char overlap).
- BM25 hard-negatives are strong but not adversarial human negatives.
- Category descriptions are CUAD question “Details” text, not independently authored rubrics.
- No Haiku comparator (by design for this run).
- ECE uses ten equal-width bins on p(gold); sample size 200 limits bin stability.
- Gold injection for measurable rank inflates Jev rank opportunity relative to pure retrieval; BM25 metrics use pre-injection ranks.

## Reproducibility

```bash
python scripts/prepare_cuad.py          # requires data/raw/CUAD_v1/CUAD_v1.json
python scripts/build_gold_pairs.py      # freezes pairs; do not mutate after scoring
python score.py --concurrency 6
python score.py --only-ablation --concurrency 6
python scripts/analyze_gates.py
python scripts/plot_figures.py
```

Environment: `TYPESAFE_API_KEY`. Seed `20260920`. Cache: `runs/jev/cache/`.
