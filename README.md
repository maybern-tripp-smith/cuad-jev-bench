# cuad-jev-bench

Open-data **TypeSafe/Jev** evaluation of CUAD contract-clause relevance (FedLock / fedjev-style protocol).

| | |
|--|--|
| **run_id** | `cuad-jev-2026-09-20` |
| **criterion** | `more relevant to the requested contract category` |
| **model** | `jev-latest` → `jev-1.13.0` |
| **corpus** | [CUAD](https://huggingface.co/datasets/theatticusproject/cuad) (CC BY 4.0) |
| **labels** | Human CUAD spans only |
| **Pages** | [`docs/`](docs/) |

## Headline results

| Gate | Result |
|------|--------|
| 1 Easy-pair inversion ≤ 0.05 | **PASS** (0.00) |
| 2 Labeled inversion + Brier | report (inv≈0.32, Brier≈0.25) |
| 3 Jev MRR > BM25 MRR | **PASS_SIGNAL** (0.917 > 0.469) |
| 4 mean Score(gold) > mean Score(neg) | **PASS** |
| 5 Brier / ECE | report |
| 6 Name/meta Δ inversion ≤ 0.05 | **PASS** (Δ=0.00) |
| 7 Literature DeBERTa | report only (not re-run) |

Total Jev cost ≈ **$0.043**; p50 latency ≈ **182 ms**. Details: [`REPORT.md`](REPORT.md), [`ANALYSIS.md`](ANALYSIS.md).

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
```

## Layout

```
data/raw|clean|labels|pairs|stats/
runs/jev/cache/
results/          # gates, cost, timing, figures
scripts/
docs/             # GitHub Pages
```

## License

- **Code & analysis:** MIT (`LICENSE`)
- **CUAD contract text:** CC BY 4.0 — see `DATA.md` and cite Hendrycks et al. (2021)

## Citation

See `CITATION`.
