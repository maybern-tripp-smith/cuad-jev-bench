# DATA.md — CUAD sources and license

## Primary corpus

**Contract Understanding Atticus Dataset (CUAD) v1**  
Atticus Project / Hendrycks et al. (NeurIPS 2021 Datasets & Benchmarks).

| Item | Value |
|------|-------|
| HuggingFace | [`theatticusproject/cuad`](https://huggingface.co/datasets/theatticusproject/cuad) |
| Project | https://www.atticusprojectai.org/ |
| Paper | https://arxiv.org/abs/2103.06268 |
| File used | `CUAD_v1/CUAD_v1.json` (SQuAD-format) |
| **License** | **Creative Commons Attribution 4.0 International (CC BY 4.0)** |

Derivative paragraph chunks and pair indices in this repository are released under the
same attribution requirement for the underlying CUAD text. This bench’s code and
analysis artifacts are MIT (see `LICENSE`); CUAD contract text remains CC BY 4.0.

## What we derive

| Artifact | Description |
|----------|-------------|
| `data/clean/paragraphs.jsonl` | Paragraph-ish chunks (~≤400 tok / ≤1600 chars) with char offsets |
| `data/clean/categories.json` | 41 CUAD category names + “Details” descriptions from questions |
| `data/labels/spans.jsonl` | Human answer spans only (never model-generated labels) |
| `data/pairs/*` | Seed-fixed Stratum A/B pairs + candidate queries |
| `data/stats/corpus_stats.json` | Corpus size / length / category histogram |

## Attribution (CC BY 4.0)

> Contract Understanding Atticus Dataset (CUAD), The Atticus Project.  
> Hendrycks, Burns, Chen, Ball. *CUAD: An Expert-Annotated NLP Dataset for Legal Contract Review*, NeurIPS 2021.

## Exclusions

No customer contracts, Maybern tenant data, Slack, or proprietary corpora are used.
