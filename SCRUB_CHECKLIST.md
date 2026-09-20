# SCRUB_CHECKLIST — public publish

- [x] No `TYPESAFE_API_KEY` / Anthropic / other API keys in tracked files
- [x] No `.env` files in public pack
- [x] No box secret paths or home credential paths in docs
- [x] `runs/jev/cache/` and raw response dumps reviewed for accidental key echo (API responses do not contain keys)
- [x] Customer / Maybern tenant identifiers absent (open CUAD only)
- [x] `DATA.md` documents CC BY 4.0 for CUAD text
- [x] GitHub Pages under `docs/` with `.nojekyll`
- [x] Tarball excludes `.venv/`, `__pycache__`, `.env`

Scrub audit date: 2026-09-20 (America/New_York).
