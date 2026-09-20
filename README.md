# cuad-jev-bench

This repository is a pre-registered test of a **structured** contract-clause judge on an open set of commercial contracts. It is written so a reader fluent in finance and ordinary empirical work — not in legal natural-language processing — can rebuild the measurement.

**The corpus.** The Contract Understanding Atticus Dataset (CUAD), released by the Atticus Project (Hendrycks, Burns, Chen, and Ball, 2021; Creative Commons Attribution 4.0), contains **510** contracts and human marks for **41** clause categories (**13,823** marked spans). Categories are diligence questions a reader would search for: governing law, cap on liability, anti-assignment, license grant, and so on. Gold is those human spans only.

**The judge.** TypeSafe Jev returns *typed* judgments — a **Choice** (which of two texts is more relevant to a requested category, with probabilities) or a **Score** (one of four relevance levels with a probability on each level) — not a chat paragraph. The frozen criterion is `more relevant to the requested contract category`. The judge never writes gold.

**The cheap baseline.** Best Match 25 (BM25) is a keyword-overlap ranker. We use it to propose same-contract look-alike distractors (**hard negatives**) and as a ranking baseline. If the judge cannot beat word overlap, the bench is not showing more than lexical match.

**What is scored.** **Stratum A** (n=40) is an easy pair: a marked span versus a paragraph from a contract that has no mark for that category. **Stratum B** (n=200) is a hard pair: a marked span versus a Best Match 25 distractor in the same contract. An **inversion** is the judge reversing the human label after both presentation orders are averaged. **Construct validity** (Gate 4) asks whether, under the same category question, mean Score on marked spans exceeds mean Score on those distractors. **Mean reciprocal rank** is the average of 1/(rank of gold) over 100 queries; **recall at *k*** is the share of queries with gold in the top *k*. **Brier score** is mean squared error of *p*(gold). **Expected calibration error** is a binned gap between predicted probability and an observed frequency.

**What “pass” means.** Seven **gates** were registered before any live call. Gates 1, 3 (signal), 4, and 6 have pass/fail or signal lines. Gates 2, 5, and 7 are report-only. Gate 7 cites published extractive numbers from a DeBERTa-xlarge model (area under the precision–recall curve 47.8; precision at 80% / 90% recall 44.0 / 17.8; Jaccard ≥ 0.5 is that paper’s span-overlap rule). **We did not re-run DeBERTa.** Uncertainty is a standard error (s.e.), never STE.

| | |
|--|--|
| **run_id** | `cuad-jev-2026-09-20` |
| **criterion** | `more relevant to the requested contract category` |
| **model** | `jev-latest` → `jev-1.13.0` |
| **corpus** | [CUAD](https://huggingface.co/datasets/theatticusproject/cuad) (CC BY 4.0) |
| **labels** | Human CUAD spans only |
| **Pages** | [https://maybern-tripp-smith.github.io/cuad-jev-bench/](https://maybern-tripp-smith.github.io/cuad-jev-bench/) |

The public Pages site starts with a [How to read this report](https://maybern-tripp-smith.github.io/cuad-jev-bench/) glossary. A separate [scoreboard guide](https://maybern-tripp-smith.github.io/cuad-jev-bench/how-to-read.html) says what PASS means, what would count as strong or weak on this design, and what the numbers do not prove. Companions: [`OVERVIEW.md`](OVERVIEW.md), [`HOW_TO_READ.md`](HOW_TO_READ.md), [`REPORT.md`](REPORT.md), [`ANALYSIS.md`](ANALYSIS.md).

## Selected estimates

| Gate | Estimate |
|------|----------|
| 1 Easy-pair inversion ≤ 0.05 | **PASS** — 0.000 (n=40, s.e. 0.000) |
| 2 Labeled inversion + Brier | report — inversion 0.320 (s.e. 0.033); Brier 0.250 (s.e. 0.026) |
| 3 Jev mean reciprocal rank > Best Match 25 | **PASS_SIGNAL** — 0.917 (s.e. 0.021) > 0.469 (s.e. 0.041) |
| 4 mean Score(gold) > mean Score(negatives) | **PASS** — gap 2.130 (s.e. 0.067) |
| 5 Brier / expected calibration error | report — expected calibration error 0.324 |
| 6 Name/meta change in inversion ≤ 0.05 | **PASS** — change 0.000 |
| 7 Literature DeBERTa | report only (not re-run) |

Total Jev cost ≈ **$0.043**; median (50th percentile) latency ≈ **182 milliseconds**. Details: [`REPORT.md`](REPORT.md), [`ANALYSIS.md`](ANALYSIS.md), [`results/diagnostics.json`](results/diagnostics.json).

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
# or: uv sync
# place CUAD_v1.json under data/raw/CUAD_v1/ (see DATA.md)
export TYPESAFE_API_KEY=...
python scripts/prepare_cuad.py
python scripts/build_gold_pairs.py   # freeze gold BEFORE scoring
python score.py --concurrency 6
python score.py --only-ablation --concurrency 6
python scripts/analyze_gates.py
python scripts/plot_figures.py
python scripts/render_docs.py
```

Dependencies live in `pyproject.toml` (PEP 621). This published run is already scored; the commands are the reconstruction path. Do not mutate frozen gold. Do not treat Gate 7 as a command that runs DeBERTa.

## Layout

```
data/raw|clean|labels|pairs|stats/
runs/jev/cache/
results/          # gates, diagnostics, cost, timing, figures
scripts/
docs/             # GitHub Pages
pyproject.toml    # install: pip install -e .  or  uv sync
```

## License

- **Code & analysis:** MIT (`LICENSE`)
- **CUAD contract text:** CC BY 4.0 — see `DATA.md` and cite Hendrycks et al. (2021)

## Citation

See `CITATION`.
