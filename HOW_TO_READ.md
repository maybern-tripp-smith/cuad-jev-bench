# How to read these results

This page is a **scoreboard guide**. It is not a second analysis and it is not the reconstruction manual. After one pass you should be able to open [`REPORT.md`](REPORT.md) or `results/gates.json` and know, for each line, what question was asked, whether a pre-registered pass line applies, and what would have counted as strong, weak, or inconclusive **on this design**.

The numbers below are the observed figures from run `cuad-jev-2026-09-20`. They are copied from the [Report](REPORT.md) and from `results/gates.json`. Nothing here is a product claim. Uncertainty is a **standard error** (written “s.e.”). We never use the letters STE. The machine-readable files store that same quantity under the key `ste`.

If you need the corpus, the pair-construction rules, or the reconstruction commands, start with the [Overview](OVERVIEW.md). Methods, the full figure set, and limitations are in the [Analysis](ANALYSIS.md).

## If you only look at three numbers

These three decide whether the pre-registered design worked on this run. They are not a product claim.

| Look at | Number on this run | Why it is the headline |
|---------|--------------------|------------------------|
| Easy-pair inversion (Gate 1) | **0.000** (n=40, s.e. 0.000), **PASS** | On the 40 obvious pairs, the judge never reversed the human label. A structured judge that fails the easy pairs is not ready for the hard ones. |
| Mean reciprocal rank versus Best Match 25 (Gate 3) | **0.917** (s.e. 0.021) versus **0.469** (s.e. 0.041), **PASS_SIGNAL** | When ten keyword candidates are re-ranked, the marked paragraph sits much nearer the top under Jev Score than under word-overlap. Chance among those lists is 0.298. |
| Score gap, gold minus hard-negative (Gate 4) | **2.130** (s.e. 0.067), **PASS** | Under the same category question, mean expected Score on marked spans (2.685) exceeds the mean on keyword distractors (0.555). That is the construct-validity check, not a retrieval slogan. |

The other four gates are either report-only (2, 5, 7) or a robustness check that names and dates are not doing the work (6: change in inversion **0.000**). Read them after these three.

## What this scoreboard is

The **Contract Understanding Atticus Dataset** (CUAD, pronounced “quad”) is 510 public commercial contracts with human marks for 41 clause categories (13,823 spans), released by the Atticus Project (Hendrycks, Burns, Chen, and Ball, 2021; Creative Commons Attribution 4.0). **Gold** is those human-marked spans only. The judge never writes a label.

**TypeSafe** is an application programming interface for *typed* judgments (a structured object, not a chat paragraph). **Jev** is the judge model. This run requested `jev-latest`; live responses resolved to **`jev-1.13.0`**. The frozen criterion, never paraphrased in the call, is:

`more relevant to the requested contract category`

Two typed endpoints appear on the scoreboard.

**Choice.** Two texts, one category. The API returns a winner and probabilities. Each pair is shown twice, with the sides swapped, so a preference for whichever snippet is on the left cannot decide the outcome. The two probabilities are mapped onto the gold side and averaged. That average is **p(gold)**.

**Score.** One paragraph and four ordered levels — `irrelevant`, `weakly relevant`, `relevant`, `highly relevant`. The **expected score** is the probability-weighted level index (0 through 3).

**Best Match 25** (BM25) is a 1990s keyword ranking formula. It scores a paragraph by how often the query’s words appear, discounted by how common those words are and by paragraph length. It does not parse contracts. This bench uses it to pick same-contract look-alike distractors and as the ranking baseline. If the structured judge cannot beat “count the overlapping words,” the scoreboard is not showing more than lexical match.

Two measurement ideas are easy to mix up:

1. **Annotation / location** — did a system recover the same characters a human highlighted? That is extractive overlap.
2. **Relevance** — given a category description, is text A more on-point than text B? That is this bench.

A nearby paragraph can share words with a *Cap On Liability* clause without being the cap. Keyword hit-rate and span overlap do not, by themselves, say that a model judged relevance.

## Pass versus a reported diagnostic

Seven **gates** were written into `REPORT.md` at 17:30:16 EDT on 20 September 2026, **before** any Jev call. Gold pairs were frozen at 17:32:37 EDT. A pass line that was not registered before those calls is not a fail, and it is not a pass.

| Label on the table | What it means | Which gates |
|--------------------|---------------|-------------|
| **PASS** / **FAIL** | A numeric line was registered in advance. The observed number is on the passing side of that line, or it is not. | 1 (inversion ≤ 0.05), 4 (mean Score on gold > mean Score on hard negatives), 6 (change in inversion ≤ 0.05) |
| **PASS_SIGNAL** | A directional inequality was registered, not a numeric cutoff. Jev’s mean reciprocal rank of gold must exceed Best Match 25’s. | 3 |
| **report** | No pass line. The number is a diagnostic you are meant to read, not a verdict. | 2 (hard-pair inversion and Brier), 5 (calibration), 7 (published DeBERTa extractive numbers) |

**PASS** means only that the pre-registered line was met. It does not mean the model is calibrated, that it reads a full contract, or that it beat a published extractive system. **report** means you should not invent a pass/fail after seeing the number.

## What each gate asks

**Gate 1 — easy pairs (pass/fail).** On 40 **Stratum A** pairs — a marked span versus a paragraph from a *different* contract that has **no** human mark for that category — does the judge reverse the human label on more than 5 percent of pairs? The registered question is: can it do the obvious cases? Result: inversion **0.000** (n=40, s.e. 0.000). **PASS**. Zero inverted identifiers.

**Gate 2 — hard pairs (report).** On 200 **Stratum B** pairs — a marked span versus the highest Best Match 25 paragraph in the *same* contract that does not overlap the gold character range — how often does it reverse, and how sharp are the probabilities? No pass line: this is the difficult same-contract setting, not a second easy test. Result: inversion **0.320** (s.e. 0.033) — 64 of 200 pairs; mean Brier **0.250** (s.e. 0.026); mean *p*(gold) **0.676**.

**Gate 3 — ranking versus Best Match 25 (signal).** On 100 (contract, category) queries, each with up to ten candidate paragraphs, is Jev’s **mean reciprocal rank** of the marked paragraph higher than Best Match 25’s? Result: **0.917** (s.e. 0.021) versus **0.469** (s.e. 0.041); chance **0.298** (s.e. 0.002). Recall at 1 / 3 / 5: Jev 0.86 / 0.97 / 0.99 versus Best Match 25 0.35 / 0.51 / 0.57. **PASS_SIGNAL**.

**Gate 4 — Score separation (pass/fail).** Under the **same** category question, is mean expected Score on gold spans higher than mean expected Score on Best Match 25 hard negatives? That is the **construct-validity** check: does the Score axis move with category relevance, not merely with shared words? Result: gold **2.685** (s.e. 0.062, n=100) versus negatives **0.555** (s.e. 0.027, n=882); gap **2.130** (s.e. 0.067). **PASS**.

**Gate 5 — calibration (report).** On the 200 hard pairs, how far is *p*(gold) from the gold-as-correct label? **Brier score** **0.250** (s.e. 0.026); **expected calibration error** **0.324** (n=200). No pass line.

**Gate 6 — name ablation (pass/fail).** Re-run the 40 easy pairs with party names and dates left in. Does the inversion rate move by more than 0.05? The registered question is: was Gate 1 an artifact of matching letterhead? Result: stripped 0.000, names-in 0.000, change **0.000**. **PASS**.

**Gate 7 — literature DeBERTa (report only).** Publish three extractive numbers from Hendrycks et al. (2021) for a **DeBERTa-xlarge** model (Decoding-enhanced Bidirectional Encoder Representations from Transformers, extra-large size) that *highlights character spans* in a full contract. Area under the precision–recall curve **47.8**; precision at 80 percent recall **44.0**; precision at 90 percent recall **17.8**. **Not a re-run.** Different task shape. Not a within-bench baseline.

## How to read the numbers

### Inversion

Each Choice pair is shown in both orders. If the averaged *p*(gold) is below 0.5, the implied winner is the distractor. That event is an **inversion**: the judge reversed the human label. The inversion rate is the share of pairs on which that happens.

**0.000 on 40 easy pairs** means none of those pairs inverted. **0.320 on 200 hard pairs** means 64 inverted. The second number is larger because the distractor was chosen to look like the marked span, not because Gate 2 “failed.” There was no Gate 2 pass line.

An **order-flip** is narrower: the discrete winner in the A-then-B showing disagrees with the winner in the B-then-A showing. Stratum A: 0 of 40. Stratum B: 0.075 (15 of 200).

### Brier score

**Brier score** is mean squared error of a probability. This bench treats the gold span as the correct side on every pair (label *y* = 1). On one pair the contribution is (*p*(gold) − 1)².

| If the judge says… | Brier contribution | Reading |
|--------------------|-------------------:|---------|
| *p*(gold) = 1.0 | 0 | Certain, and on the gold side |
| *p*(gold) = 0.5 | 0.25 | A coin flip |
| *p*(gold) = 0.0 | 1 | Certain, and inverted |

Stratum A mean Brier is **0.007** (s.e. 0.004): near-certain and almost never inverted. Stratum B mean Brier is **0.250** (s.e. 0.026): on average no sharper than a constant 0.5, even though mean *p*(gold) is 0.676, because the 64 inversions are costly when the judge is confident on the wrong side. Gate 5 reports the same 0.250 as a calibration diagnostic, not as a ranking score.

### Mean reciprocal rank

For each of the 100 ranking queries, find the position of the first human-marked paragraph (1 = top of the list). **Reciprocal rank** is 1 divided by that position: rank 1 → 1.0; rank 2 → 0.5; rank 10 → 0.1. If gold is missing from the keyword list, Best Match 25’s reciprocal rank is 0.

**Mean reciprocal rank** averages those 1/rank values across the 100 queries. It rewards putting gold near the top and is not fooled by a system that is merely “somewhere in the ten.”

Jev **0.917** (s.e. 0.021) versus Best Match 25 **0.469** (s.e. 0.041) is the Gate 3 signal. The gap, 0.448, is large relative to the two reported standard errors (about 0.021 and 0.041). We do not compute a separate significance test in `gates.json`; read the two means and their standard errors, not a *p*-value we did not publish.

**Gold injection.** On 28 of the 100 queries, no gold paragraph appeared in the Best Match 25 top 10. One gold paragraph was then inserted so Jev’s rank is measurable, and `gold_injected = true` is logged. Injection is **not** counted as keyword-retrieval success: Best Match 25 ranks use the pre-injection position (those 28 sit between 11 and 204). Jev always sees gold among the scored ten; the keyword baseline does not get that gift. Mean reciprocal rank here is therefore a re-ranking contrast on a shortlist, not “Jev retrieved the clause from the whole contract.”

### Recall at *k*

**Recall at k** is the share of the 100 queries for which a gold paragraph appears in the top *k* of the ranked list. Recall at 1 is “was gold first?” Recall at 5 is “was gold somewhere in the first five?” Chance among ten equally likely slots is *k*/10 (0.10, 0.30, 0.50).

On this run: Jev 0.86 / 0.97 / 0.99 at *k* = 1 / 3 / 5 versus Best Match 25 0.35 / 0.51 / 0.57. Read recall at 1 next to mean reciprocal rank. A system can have high recall at 5 and a mediocre mean reciprocal rank if gold is usually present but rarely first. That is closer to the keyword column than to Jev’s.

### Score gaps

Expected Score lives on 0 to 3. Gate 4 compares two means under the same category question: 100 gold spans versus 882 hard-negative paragraphs. The **gap** is 2.685 − 0.555 = **2.130** (s.e. 0.067). On a 0-to-3 axis, a gap of 2.13 with a standard error of 0.067 is a clean separation: gold sits near “highly relevant,” the keyword distractors sit between “irrelevant” and “weakly relevant.”

The category-level panel in the [Analysis](ANALYSIS.md) repeats that contrast per Atticus category. Bars with few queries are noisy; do not promote a single category bar into a finding.

### Cost and latency

These are operations numbers, not quality numbers. They answer “what did the published run cost to score?” not “how well did the judge work?”

| Quantity | Observed | Source |
|----------|----------|--------|
| Total spend | **$0.043149** | 1,542 logged calls; 1,027,363 input tokens at $0.042 per million input tokens; output free (`results/cost.json`) |
| Largest slice | $0.026772 | 982 candidate Score calls (637,421 input tokens) |
| Median (50th percentile) latency | **182 milliseconds** | `results/timing.json`; mean 191.1 ms; 95th percentile 258 ms; concurrency 6 |

Preflight estimated $0.050. The published run came in under that estimate. A cheaper run would not make Gate 2 look better.

### Standard errors

**Rates** (inversion, order-flip, recall at *k*): binomial standard error √[*p*(1 − *p*)/*n*]. Forty zeros have standard error 0.

**Means** (Brier, expected Score, mean reciprocal rank): sample standard deviation over √*n*, with a 1,000-draw bootstrap standard error retained in `gates.json` where it was already computed.

**Gate 4 gap.** The diagnostic file also stores √(s.e._gold² + s.e._neg²); the table’s 0.067 is the bootstrap gap standard error.

A gap many times its standard error is evidence of separation on *this* sample. It is not a claim about every Atticus category or about a different pair-construction rule.

## Strong, weak, and inconclusive on this design

The pass lines are the ones that were registered. “Strong” here means the observed number sits well inside a registered line, or the registered inequality is large relative to the reported standard errors. It does not mean “ready for production contract review.”

**What would count as strong on this design**

- Gate 1 inversion at or under 0.05, and preferably near 0. Observed: **0.000**.
- Gate 3 Jev mean reciprocal rank above Best Match 25 by a gap that is large relative to the two standard errors, not a 0.01 difference on noisy estimates. Observed: **0.917** versus **0.469**.
- Gate 4 Score gap clearly above zero relative to its standard error, with gold mean well above the distractor mean on the 0-to-3 axis. Observed: gap **2.130** (s.e. 0.067).
- Gate 6 change in inversion at or under 0.05. Observed: **0.000**.

On those four registered checks, this run is on the strong side of the design it wrote down.

**What would count as weak on this design**

- Gate 1 inversion above 0.05: the judge reverses obvious gold-versus-unrelated pairs.
- Gate 3 Jev mean reciprocal rank at or below Best Match 25: Score adds no ranking signal over word overlap.
- Gate 4 gap consistent with zero or negative: the Score axis does not separate marked spans from keyword distractors under the same category question.
- Gate 6 change above 0.05: easy-pair success may be letterhead matching.

None of those weak patterns is what this run shows.

**What is inconclusive — do not promote these into a verdict**

- **Gate 2 inversion 0.320.** About one hard pair in three inverts. That is the intended difficult setting. There is no pass line. A rate near 0 on Stratum B would have suggested the hard negatives were not hard. A rate near 0.5 would have suggested no discrimination. 0.320 sits between those stories; it is a diagnostic of difficulty, not a hidden fail.
- **Gate 5 Brier 0.250 and expected calibration error 0.324.** These say assigned *p*(gold) is not near-certain on hard pairs (and Gate 5’s 0.324 uses the gold-as-correct convention, *y* = 1). The reliability figure’s printed number uses discrete correctness (1 minus inversion) and is 0.109 in `results/diagnostics.json`. Neither number is a ranking verdict. We did not fit a temperature after the fact.
- **Gate 7 DeBERTa 47.8 / 44.0 / 17.8.** Published extractive numbers from a different task. They tell you the original highlighting problem is hard. They do not score Jev.
- **Category bars with few pairs.** The Analysis figure keeps categories with at least three Stratum B pairs; those standard errors are still wide. Do not rank “Jev is good at Insurance, bad at Volume Restriction” from one bar.
- **Cost and latency.** $0.043 and 182 milliseconds describe the published scoring bill.

## What these results do not prove

Read this list before quoting a PASS in a memo.

- **They do not prove that Jev beat DeBERTa.** Gate 7 copies published extractive numbers (Hendrycks et al., 2021). DeBERTa-xlarge was trained to highlight character spans in a full contract. This bench scores already-cut excerpts and pairwise Choice. We did not re-run DeBERTa. Area under the precision–recall curve 47.8 is not a Jev metric.
- **They do not prove full-contract question answering.** Candidates are paragraph-ish chunks (target ≤1,600 characters). Gold spans that cross a chunk boundary are mapped by character overlap. The judge never sees the whole agreement as one document. Excerpt design is not extractive span highlighting, and it is not a lawyer reading the PDF.
- **They do not prove retrieval from a raw contract.** On 28 of 100 ranking queries, gold was inserted into the scored ten so Jev’s rank is measurable. Best Match 25 is scored on the pre-injection list. Gate 3 is a re-ranking contrast, not “the model found the clause in 21,598 paragraphs.”
- **They do not prove the probabilities are well calibrated.** Gate 5 is report-only. Expected calibration error 0.324 (*y* = 1) says *p*(gold) sits well short of certainty that the marked span is the more relevant text. We report that without a pass line and without a post-hoc recalibration.
- **They do not prove the distractors were the hardest a human could write.** Hard negatives are Best Match 25 look-alikes in the same contract, not adversarially authored near-misses.
- **They do not prove a legal-advice or diligence-quality claim.** The criterion is relevance to an Atticus category prompt, not “would counsel rely on this.”
- **They do not prove every category.** Forty-one Atticus categories are unevenly represented; rare categories are noisy. Seed `20260920` fixed the pair draw.
- **They do not prove a different judge, a chat model, or a later `jev-latest` pin.** The resolved model is `jev-1.13.0`. Main tables do not use Haiku or Grok-as-judge.

## Where to look next

| If you want… | Open |
|--------------|------|
| Terms, pair construction, reconstruction steps | [Overview](OVERVIEW.md) |
| Methods, all figures, interpretation, limitations | [Analysis](ANALYSIS.md) |
| Gate table, freeze timestamps, cost by slice | [Report](REPORT.md) |
| Machine-readable gates and diagnostics | `results/gates.json`, `results/diagnostics.json`, `results/cost.json`, `results/timing.json` |
| Figure captions | [`results/figures/CAPTIONS.md`](results/figures/CAPTIONS.md) |
| How the pairs were frozen | [`data/pairs/PAIR_MANIFEST.md`](data/pairs/PAIR_MANIFEST.md) |
