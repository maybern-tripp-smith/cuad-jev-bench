# ANALYSIS — cuad-jev-bench

**run_id:** `cuad-jev-2026-09-20`
**model:** `jev-1.13.0` (requested `jev-latest`)
**criterion (exact):** `more relevant to the requested contract category`
**repository:** [maybern-tripp-smith/cuad-jev-bench](https://github.com/maybern-tripp-smith/cuad-jev-bench)
**pages:** [https://maybern-tripp-smith.github.io/cuad-jev-bench/](https://maybern-tripp-smith.github.io/cuad-jev-bench/)

Companion gate report: [`REPORT.md`](REPORT.md). Landing-page glossary: [`OVERVIEW.md`](OVERVIEW.md). Machine-readable results: [`results/gates.json`](results/gates.json), [`results/diagnostics.json`](results/diagnostics.json). Figure captions: [`results/figures/CAPTIONS.md`](results/figures/CAPTIONS.md).

## How to read this analysis

This note is written so a mid-career economist — fluent in private-equity language and ordinary applied statistics, not in legal natural-language processing — can rebuild the measurement from the prose. Every short label used in a table below is taught in this section before the abstract uses it. Uncertainty is a **standard error** (s.e.), never written STE. Observed counts, dollars, and file times are from this run; we do not invent a metric or a DeBERTa number.

**The corpus.** The **Contract Understanding Atticus Dataset** (CUAD) is 510 public commercial contracts released by the **Atticus Project** (Hendrycks, Burns, Chen, and Ball, 2021; Creative Commons Attribution 4.0). Lawyers marked **13,823 spans** — contiguous character ranges — as answers to **41 category** questions (governing law, cap on liability, anti-assignment, license grant, and so on). We split the contracts into **21,598** paragraph-ish chunks (target ≤1,600 characters). Category prompts are the Atticus “Details” text in `data/clean/categories.json`. Gold is those human spans only.

**Two constructs.** An *annotation / location* measure asks whether a system recovered the same characters a human highlighted. A *relevance* measure asks whether, given a category description, one text is more on-point than another. This bench is the second. Nearby paragraphs often share vocabulary with a marked clause without being the clause.

**The judge.** **TypeSafe** is an application programming interface that returns *typed* judgments (a structured object), not a chat paragraph. **Jev** is the judge model (`jev-latest` → `jev-1.13.0`). **Choice** takes Text A, Text B, and the frozen criterion, and returns a winner plus *p*(A), *p*(B). **Score** takes one paragraph and four levels — irrelevant / weakly relevant / relevant / highly relevant — and returns a probability on each level. **Expected score** is 0·*p*(irrelevant) + 1·*p*(weakly relevant) + 2·*p*(relevant) + 3·*p*(highly relevant), so it lives on 0 to 3.

**The keyword baseline.** **Best Match 25** (BM25) is a keyword-overlap ranker: it scores a paragraph by query-word frequency, discounted by how common those words are and by paragraph length. It does not understand contracts. We use `rank_bm25.BM25Okapi` as (i) a source of look-alike distractors and (ii) a ranking baseline. If Jev cannot beat word overlap, the bench is not showing more than lexical match.

**Hard negatives and strata.** A *negative* is a paragraph that is not the marked span for the requested category. A **hard negative** is a negative a keyword ranker would surface (same contract, shared vocabulary). **Stratum A** (n=40) pairs a gold span with a paragraph from a *different* contract that has *no* mark for that category — a certain, easy contrast. **Stratum B** (n=200) pairs a gold span with the highest Best Match 25 non-overlapping paragraph in the *same* contract — the hard contrast. Seed `20260920`. A third slice, 100 (contract, category) **candidate queries**, takes Best Match 25’s top 10 paragraphs; if gold is missing (28 of 100 queries), we inject one gold paragraph so Jev’s rank is measurable and we do **not** count that as keyword success.

**Inversion.** Each Choice pair is shown in both orders. Probabilities are mapped onto the gold side and averaged (**p(gold)**). If that average is below 0.5, the implied winner is the distractor — an **inversion**. The inversion rate is the share of such pairs. An **order-flip** is disagreement between the two presentation orders’ discrete winners.

**Construct validity.** A score has construct validity when it moves with the thing you claim to measure. Gate 4 asks whether, under the *same* category question, mean expected Score on gold spans exceeds mean expected Score on hard negatives. That is a measurement check, not a retrieval-quality claim.

**Brier score.** Mean squared error of a probability. Label *y* = 1 (gold is the correct side by construction). One pair: (*p*(gold) − 1)². Average over pairs. 0 is perfect; 0.25 matches a constant 0.5; 1 is a confident inversion.

**Reliability and expected calibration error.** A reliability diagram bins predicted *p*(gold) and plots mean prediction against an observed frequency. **Expected calibration error** is the probability-weighted absolute gap across ten equal-width bins. Gate 5’s table number **0.324** uses *y* = 1 (the Brier convention). The reliability figure’s vertical axis is the share of pairs whose discrete winner was gold (1 minus inversion); the number printed on that figure is 0.109 in `results/diagnostics.json`. We do not temperature-fit after the fact.

**Mean reciprocal rank and recall at k.** Rank of gold = position of the first marked paragraph (1 = top). Reciprocal rank = 1/rank. **Mean reciprocal rank** averages that over the 100 queries. **Recall at k** is the share of queries with gold in the top *k*. Chance recall among ten slots is *k*/10.

**DeBERTa (literature only).** Hendrycks et al. (2021) report extractive numbers for a **DeBERTa-xlarge** model that highlights character spans — a different task. Published: area under the precision–recall curve 47.8; precision at 80% recall 44.0; precision at 90% recall 17.8. **Jaccard ≥ 0.5** (two spans match if intersection-over-union is at least one half) is cited as that literature’s overlap rule; we do not recompute it. **We did not re-run DeBERTa.**

**Standard errors.** Rates: binomial √[*p*(1−*p*)/*n*]. Means and Brier: sample standard deviation / √*n* (bootstrap s.e. retained in `gates.json` where previously computed). Gate 4 gap s.e. = √(s.e._gold² + s.e._neg²) in the diagnostic file; the table also stores a bootstrap gap s.e.

## Abstract

Human marks of contract clauses are a natural but incomplete label for *relevance to a requested legal category*: the same category string can apply to sparse spans in a long commercial agreement, while nearby paragraphs share vocabulary without being on-point. This note reports a pre-registered evaluation of TypeSafe Jev on the open Contract Understanding Atticus Dataset under a frozen pairwise Choice and graded Score protocol. Labels are Atticus human spans only; the judge is never used to construct gold.

On 40 rule-built certain pairs (Stratum A), Choice inversion is 0.000 (binomial standard error 0.000). On 200 same-contract Best Match 25 hard-negative pairs (Stratum B), inversion is 0.320 (s.e. 0.033) with mean Brier score 0.250 (s.e. 0.026) and expected calibration error 0.324 under the gold-as-correct convention. For 100 (contract, category) candidate-ranking queries, expected Score yields gold mean reciprocal rank 0.917 (s.e. 0.021) versus Best Match 25 0.469 (s.e. 0.041) and chance 0.298 (s.e. 0.002). Gate 4 is a construct-validity contrast: under the same category question, mean expected Score on gold spans (2.685, s.e. 0.062) exceeds the mean on hard negatives (0.555, s.e. 0.027), a gap of 2.130 (s.e. 0.067). Leaving party names and dates in Stratum A leaves inversion unchanged (change = 0.000). Gate 7 cites published DeBERTa-xlarge extractive metrics as a literature difficulty anchor only; this bench does not re-run DeBERTa and uses a different task shape. Total Jev spend is $0.043149; median (50th percentile) latency is 182 milliseconds.

## What this bench adds

1. An open-data Jev bench for contract-clause *relevance* with pre-registered gates, frozen gold, cost and latency artifacts, and diagnostic figures.
2. Design A: certain cross-contract negatives (Stratum A) plus same-contract Best Match 25 hard negatives (Stratum B), Choice in both presentation orders.
3. Candidate-score lite: Best Match 25 top-10 re-ranked by Jev Score levels, with gold injection logged when needed for measurable rank (28 of 100 queries).
4. An explicit construct-validity gate (Gate 4): gold versus non-gold under the same category question, with standard errors.
5. An honest Gate 7: literature extractive DeBERTa numbers for difficulty narrative only — not a re-run and not a like-for-like task comparison.

## 1. Introduction

Empirical work on contract understanding often treats extractive span overlap or retrieval hit-rate as sufficient evidence that a model “understands” a category. Those measures conflate the two constructs taught above: location of a highlight versus relevance of a text unit.

The evaluation question is therefore the three-part relevance question in the “How to read” section: easy orderings, hard-negative discrimination with calibration reported, and a Score gap under a shared category question.

Gates were registered before any Jev output. Pass/fail applies to Gates 1, 3 (signal), 4, and 6; Gates 2, 5, and 7 are report-only.

## 2. Data

| Corpus | Path | Role |
|--------|------|------|
| CUAD v1 contracts | `data/raw/CUAD_v1/CUAD_v1.json` | Source text (CC BY 4.0) |
| Paragraph chunks | `data/clean/paragraphs.jsonl` | 21,598 units |
| Human spans | `data/labels/spans.jsonl` | 13,823 annotations across 41 categories |
| Frozen gold | `data/pairs/gold_pairs.jsonl` | Strata A/B + candidate queries |

**Labels.** Atticus human spans only. Category prompts use CUAD question “Details” text.

**Exclusions / design choices (pre-registered).** No post-hoc dropping of inverted Stratum A pairs. Candidate scoring injects gold into the Best Match 25 top-10 when absent so rank is measurable; injection is logged and is not counted as keyword retrieval success. 28 of 100 queries were injected; those pre-injection keyword ranks range from 11 to 204.

**Gold freeze.** Pairs were written before the first live call (REPORT mtime 17:30:16 EDT; gold mtime 17:32:37 EDT; scoring after freeze).

![Corpus diagnostics](docs/figures/corpus_diagnostics.svg)

*Figure. Shape of the Contract Understanding Atticus Dataset after our paragraph split. Left: character-length distribution of the 21,598 chunks (target cap 1,600 characters; median 1,364). Center: number of human-marked spans per contract. Right: the fifteen most frequent of the 41 categories among 13,823 marks (Parties is the largest, 2,554 marks; Price Restrictions is among the smallest, 27). Read this as “what the corpus looks like,” not as a model result.*

## 3. Method

**Choice (primary for Gates 1–2, 6).** Criterion string (exact): `more relevant to the requested contract category`. Both presentation orders; probabilities mapped to the gold side and averaged. Inversion = averaged winner is not gold. Meta stripping via `scripts/strip_meta.py` for main tables; Gate 6 re-runs Stratum A with names and dates left in.

**Score (Gates 3–4).** Levels `irrelevant / weakly relevant / relevant / highly relevant`. Expected score = Σ *i* · *p*ᵢ with *i* ∈ {0, 1, 2, 3}.

**Strata.**

| Stratum | n | Construction |
|---------|--:|--------------|
| A | 40 | Gold span versus a paragraph from a contract with no annotation for that category |
| B | 200 | Gold span versus a Best Match 25 hard negative in the same contract (seed 20260920) |
| Candidates | 100 queries × ≤10 paragraphs | Best Match 25 top-10; gold injected if absent (28 queries) |

**Uncertainty.** Inversion and order-flip rates: binomial standard error √[*p*(1−*p*)/*n*]. Means and Brier: s.e. = sample standard deviation / √*n* (bootstrap s.e. retained in `gates.json` / `accuracy_summary.json` where previously computed). Gate 4 gap s.e. = √(s.e._gold² + s.e._neg²). Calibration: ten equal-width bins on *p*(gold); Gate 5 expected calibration error uses the gold-as-correct (*y* = 1) convention shared with Brier.

A reader who wants to redo the work, rather than re-interpret it, should follow [section 7](#7-reproducibility) in order: download CUAD → prepare paragraphs → freeze gold → Jev calls → gate script. Do not mutate the frozen gold file after scoring.

## 4. Pre-registered gates and results

| # | Gate | Pass line | Result |
|---|------|-----------|--------|
| 1 | Easy-pair inversion (A) | ≤ 0.05 | **PASS** — 0.000 (n=40, s.e. 0.000) |
| 2 | Labeled inversion + Brier (B) | report | inversion 0.320 (s.e. 0.033); Brier 0.250 (s.e. 0.026); mean *p*(gold) 0.676 (n=200) |
| 3 | Candidate Score vs Best Match 25 | Jev mean reciprocal rank > keyword mean reciprocal rank | **PASS_SIGNAL** — 0.917 (s.e. 0.021) > 0.469 (s.e. 0.041); chance 0.298 |
| 4 | Construct validity | mean Score(gold) > mean Score(negatives) | **PASS** — 2.685 (s.e. 0.062) > 0.555 (s.e. 0.027); gap 2.130 (s.e. 0.067) |
| 5 | Secondary calibration | report | Brier 0.250 (s.e. 0.026); expected calibration error 0.324 (n=200) |
| 6 | Name/meta ablation | change in inversion ≤ 0.05 | **PASS** — change 0.000 |
| 7 | Literature DeBERTa | report only | area under the precision–recall curve 47.8; precision at 80% recall 44.0; precision at 90% recall 17.8 (Hendrycks et al. 2021). **Not re-run.** |

### 4.1 Inversion by stratum

On the easy contrast, the judge never reversed the human label. On the hard contrast it reversed 64 of 200 pairs. Mean *p*(gold) falls from 0.976 on Stratum A to 0.676 on Stratum B, which is what a harder discrimination setting should look like if the distractors are doing work.

| Stratum | n | inverted | inversion (s.e.) | mean *p*(gold) | mean Brier (s.e.) | order-flip |
|---------|--:|--------:|-----------------:|---------------:|------------------:|-----------:|
| A certain | 40 | 0 | 0.000 (0.000) | 0.976 | 0.007 (0.004) | 0.000 |
| B labeled | 200 | 64 | 0.320 (0.033) | 0.676 | 0.250 (0.026) | 0.075 |

![Inversion rates](docs/figures/inversion_rates.svg)

*Figure. Choice inversion rates ± binomial standard error for Stratum A (n=40) and Stratum B (n=200). The dashed line is the Gate 1 threshold (0.05). Height is the share of pairs whose averaged winner was the distractor. Stratum A sits at 0; Stratum B sits at 0.320 (s.e. 0.033).*

![p(gold) distribution](docs/figures/p_gold_distribution.svg)

*Figure. Distribution of Choice *p*(gold) under stripped names and dates, Stratum A versus Stratum B. Vertical dashes mark stratum means (0.976 and 0.676). The leftward shift in B is the harder same-contract setting: more probability mass away from certainty that the marked span is the more relevant text.*

### 4.2 Calibration (Gate 5)

Mean Brier on Stratum B is 0.250 (s.e. 0.026) — about the score of always saying 50/50 — which is consistent with a hard task and with the 64 confident-looking inversions that pull the squared error up. Gate 5’s expected calibration error of 0.324 (*n* = 200) is the binned *y* = 1 summary taught above.

![Reliability](docs/figures/reliability_stratum_b.svg)

*Figure. Reliability diagram for Stratum B *p*(gold). Horizontal: mean predicted *p*(gold) in a ten-point-wide bin. Vertical: share of pairs in that bin whose discrete winner was the gold span (1 minus inversion). Marker area is proportional to bin count (n=200). The dashed diagonal is a perfect match of those two axes. The number printed on the figure is the bin-wise expected calibration error against that discrete-correctness axis (0.109 in diagnostics). Gate 5’s table uses the gold-as-correct convention and reports 0.324. No post-hoc temperature fitting.*

### 4.3 Candidate ranking (Gate 3)

Jev’s mean reciprocal rank of 0.917 means that, on a typical query, the marked paragraph is first or just behind first (1/1 = 1, 1/2 = 0.5; an average of 0.917 is mostly ones). Best Match 25’s 0.469 is closer to “gold often second-to-fourth, and missing from the top 10 on 28 queries.” Recall at 1 is 0.86 versus 0.35: the keyword ranker puts gold first on 35 of 100 queries; Jev does so on 86 of 100.

| Estimator | Mean reciprocal rank (s.e.) | Recall@1 (s.e.) | Recall@3 (s.e.) | Recall@5 (s.e.) |
|-----------|----------------------------:|----------------:|----------------:|----------------:|
| Jev Score | 0.917 (0.021) | 0.86 (0.035) | 0.97 (0.017) | 0.99 (0.010) |
| Best Match 25 | 0.469 (0.041) | 0.35 (0.047) | 0.51 (0.050) | 0.57 (0.051) |
| Chance | 0.298 (0.002) | 0.10* | 0.30* | 0.50* |

\*Chance recall at *k* among ten candidates is *k*/10 (deterministic benchmark).

![Mean reciprocal rank and recall](docs/figures/mrr_recall_vs_baselines.svg)

*Figure. Left: gold mean reciprocal rank under Jev Score, Best Match 25, and chance (n=100 queries) ± standard error. Right: recall at 1, 3, and 5 for Jev and Best Match 25 (± s.e.) against chance *k*/10. Best Match 25 columns use pre-injection ranks.*

![Gold rank histogram and cumulative distribution](docs/figures/gold_rank_hist_cdf.svg)

*Figure. Left: histogram of the rank of the gold paragraph (1 = highest) under Jev Score versus Best Match 25. Right: empirical cumulative distribution of those ranks — the share of queries whose gold rank is at most the value on the horizontal axis. Mass near rank 1 under Jev is recovery of annotated spans above the lexical baseline. Best Match 25 has a longer right tail, including the 28 queries where gold was outside the keyword top 10.*

### 4.4 Construct validity (Gate 4)

Gate 4 asks whether the Score axis separates gold from non-gold **under the same category query**. Mean expected Score on gold is 2.685 on the 0-to-3 scale — between “relevant” and “highly relevant.” Mean on the 882 hard-negative paragraphs is 0.555 — between “irrelevant” and “weakly relevant.” The gap 2.130 (s.e. 0.067) is the construct-validity contrast. It is not a claim that Score alone solves extractive question answering.

![Gold vs neg scores](docs/figures/gold_vs_neg_scores.svg)

*Figure. Mean expected Score on gold Atticus spans (n=100) versus Best Match 25 hard-negative paragraphs (n=882), ± standard error of the mean. Gap = 2.130 (s.e. 0.067). Horizontal categories are the two groups in Gate 4; vertical is the 0-to-3 expected-score axis.*

![Category diagnostics](docs/figures/category_diagnostics.svg)

*Figure. Left: Stratum B inversion by Atticus category (± binomial s.e.; categories with at least 3 pairs). Right: mean Score(gold) − Score(negatives) by category (± s.e. across queries), a category-level construct-validity contrast. Rare categories are noisy; do not over-read a single bar.*

### 4.5 Agreement and name ablation (Gate 6)

Order-flip rate is 0.000 on Stratum A and 0.075 on Stratum B. Leaving party names and dates in the 40 easy pairs does not change inversion (0.000 versus 0.000). The judge’s easy-pair success is not an artifact of matching letterhead.

![Agreement / ablation](docs/figures/agreement_ablation.svg)

*Figure. Left: order-flip rates for Strata A and B (± binomial s.e.) — the share of pairs whose discrete winner changed when Text A and Text B were swapped. Right: Stratum A inversion under stripped text versus names-and-dates-in text (Gate 6); change = 0.000.*

### 4.6 Cost, tokens, and latency

Total ≈ **$0.04315** over 1,542 logged calls (1,027,363 input tokens at $0.042 per million input tokens; output free). Overall latency mean 191.1 milliseconds, **median (50th percentile) 182 milliseconds**, 95th percentile 258 milliseconds (concurrency 6). Candidate Score accounts for $0.026772 of the $0.043149 — 982 of 1,542 calls.

![Cost by stratum](docs/figures/cost_by_stratum.svg)

*Figure. Dollar cost by call slice at published Jev input pricing ($0.042 per million input tokens). Slices are Choice on Stratum A stripped, Choice on Stratum A with names in, Choice on Stratum B stripped, and Score on candidate paragraphs.*

![Token usage](docs/figures/token_usage_by_stratum.svg)

*Figure. Input and output token counts by the same slices as the cost panel. Output is not billed. Input volume is dominated by the 637,421 tokens on candidate Score calls.*

![Latency by call type](docs/figures/latency_by_call_type.svg)

*Figure. End-to-end API latency in milliseconds for Choice versus Score calls. Left: overlapping histograms. Right: boxplots with extreme outliers suppressed. The published median across all timed calls is 182 milliseconds.*

### 4.7 Literature DeBERTa (Gate 7)

Published DeBERTa-xlarge extractive metrics (Hendrycks et al. 2021): area under the precision–recall curve 47.8, precision at 80% recall 44.0, precision at 90% recall 17.8. Jaccard ≥ 0.5 is that paper’s span-overlap rule; we do not recompute it. These numbers describe **extractive** difficulty on CUAD. This bench’s task is candidate scoring and pairwise relevance. Numerical comparison is narrative only. **DeBERTa is not re-run.**

## 5. Interpretation

Stratum A shows that under an easy relevance contrast, Jev Choice does not invert. Stratum B is harder: Best Match 25 negatives from the same contract share topical vocabulary, and inversion rises to 64 of 200 pairs (0.320, s.e. 0.033) — consistent with a difficult discrimination setting rather than a vacuous task. Candidate Score recovers gold paragraphs far above Best Match 25 and chance. The Gate 4 gold-minus-negative Score gap supports construct validity of the relevance Score axis under a shared category query. Calibration on Stratum B (expected calibration error 0.324 under the *y* = 1 convention) says assigned *p*(gold) sits well short of certainty that the marked span is the more relevant text; we report this without temperature fitting. Gate 7’s DeBERTa numbers remain a literature difficulty anchor, not a within-bench baseline.

## 6. Limitations

- Paragraph chunking is heuristic; gold spans may cross chunk boundaries (mapping via character overlap).
- Best Match 25 hard negatives are strong but not adversarial human negatives.
- Category descriptions are Atticus “Details” text, not independently authored rubrics.
- No Haiku comparator (by design for this run).
- Expected calibration error uses ten equal-width bins; n=200 limits bin stability. Gate 5 and the reliability figure use different observed-frequency conventions, as taught above.
- Gold injection for measurable rank inflates Jev’s rank opportunity relative to pure retrieval; Best Match 25 metrics use pre-injection ranks (28 of 100 queries injected).
- Category-level inversion estimates are noisy for rare categories.

## 7. Reproducibility

```bash
pip install -e .   # or: uv sync
# place CUAD_v1.json under data/raw/CUAD_v1/ (see DATA.md)
python scripts/prepare_cuad.py          # requires data/raw/CUAD_v1/CUAD_v1.json
python scripts/build_gold_pairs.py      # freezes pairs; do not mutate after scoring
python score.py --concurrency 6
python score.py --only-ablation --concurrency 6
python scripts/analyze_gates.py
python scripts/plot_figures.py
python scripts/render_docs.py
```

Environment: `TYPESAFE_API_KEY`. Seed `20260920`. Cache: `runs/jev/cache/`. Diagnostics: `results/diagnostics.json`. This published run is already scored; the commands are the reconstruction path. Do not mutate frozen gold. Do not treat Gate 7 as a command that runs DeBERTa — that file copies published extractive numbers.
