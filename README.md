# cuad-jev-bench

Pre-registered evaluation of **TypeSafe/Jev** on open CUAD contract text: pairwise Choice and graded Score under the fixed criterion `more relevant to the requested contract category`. The note distinguishes annotation/location measures from relevance judgments, reports standard errors (s.e.) throughout, and treats Gate 4 as construct validity (gold versus hard-negatives under the same category query). Gate 7 cites published DeBERTa extractive metrics for difficulty context only and does not re-run DeBERTa.

| | |
|--|--|
| **run_id** | `cuad-jev-2026-09-20` |
| **criterion** | `more relevant to the requested contract category` |
| **model** | `jev-latest` → `jev-1.13.0` |
| **corpus** | [CUAD](https://huggingface.co/datasets/theatticusproject/cuad) (CC BY 4.0) |
| **labels** | Human CUAD spans only |
| **Pages** | [https://maybern-tripp-smith.github.io/cuad-jev-bench/](https://maybern-tripp-smith.github.io/cuad-jev-bench/) |

## Selected estimates

| Gate | Estimate |
|------|----------|
| 1 Easy-pair inversion ≤ 0.05 | **PASS** — 0.000 (n=40, s.e. 0.000) |
| 2 Labeled inversion + Brier | report — inv 0.320 (s.e. 0.033); Brier 0.250 (s.e. 0.026) |
| 3 Jev MRR > BM25 MRR | **PASS_SIGNAL** — 0.917 (s.e. 0.021) > 0.469 (s.e. 0.041) |
| 4 mean Score(gold) > mean Score(neg) | **PASS** — gap 2.130 (s.e. 0.067) |
| 5 Brier / ECE | report — ECE 0.324 |
| 6 Name/meta Δ inversion ≤ 0.05 | **PASS** — Δ 0.000 |
| 7 Literature DeBERTa | report only (not re-run) |

Total Jev cost ≈ **$0.043**; p50 latency ≈ **182 ms**. Details: [`REPORT.md`](REPORT.md), [`ANALYSIS.md`](ANALYSIS.md), [`results/diagnostics.json`](results/diagnostics.json).

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
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

## Layout

```
data/raw|clean|labels|pairs|stats/
runs/jev/cache/
results/          # gates, diagnostics, cost, timing, figures
scripts/
docs/             # GitHub Pages
```

## License

- **Code & analysis:** MIT (`LICENSE`)
- **CUAD contract text:** CC BY 4.0 — see `DATA.md` and cite Hendrycks et al. (2021)

## Citation

See `CITATION`.
