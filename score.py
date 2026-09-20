#!/usr/bin/env python3
"""Live TypeSafe/Jev scoring for cuad-jev-bench (run_id cuad-jev-2026-09-20).

Choice (both orders) for Strata A+B; Score for candidate paragraphs;
optional --ablation-names for Gate 6 (names/dates left in).
Caches under runs/jev/cache/. No Haiku.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from scripts.load_typesafe_env import ensure as ensure_api_key  # noqa: E402
from scripts.strip_meta import strip_meta  # noqa: E402

API_NOTE = "https://api.typesafe.ai/v1/systemone"
CRITERION = "more relevant to the requested contract category"
MODEL = "jev-latest"
PRICE_PER_MTOK_INPUT = 0.042
RUN_ID = "cuad-jev-2026-09-20"

SCORE_LEVELS = [
    "irrelevant",
    "weakly relevant",
    "relevant",
    "highly relevant",
]

RUN_DIR = ROOT / "runs" / "jev"
CACHE_DIR = RUN_DIR / "cache"
ANSWERS_PATH = RUN_DIR / "answers.jsonl"
RESPONSES_PATH = RUN_DIR / "responses.jsonl"
REQUESTS_PATH = RUN_DIR / "requests.jsonl"

_write_lock = threading.Lock()
_progress_lock = threading.Lock()
_progress = {
    "n": 0,
    "cache_hits": 0,
    "failures": 0,
    "input_tokens": 0,
    "usd": 0.0,
    "resolved_model": None,
}


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def choice_cache_key(model: str, criterion: str, ha: str, hb: str, order: str, mode: str) -> str:
    raw = f"{model}|choice|{criterion}|{ha}|{hb}|{order}|{mode}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def score_cache_key(model: str, criterion: str, cat: str, ht: str) -> str:
    raw = f"{model}|score|{criterion}|{cat}|{ht}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with _write_lock:
        with path.open("a") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            f.flush()


def read_cache(key: str) -> dict[str, Any] | None:
    p = CACHE_DIR / f"{key}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def write_cache(key: str, obj: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = CACHE_DIR / f"{key}.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False))
    tmp.replace(p)


def bump_progress(*, cache_hit: bool = False, failure: bool = False, input_tokens: int = 0) -> None:
    with _progress_lock:
        _progress["n"] += 1
        if cache_hit:
            _progress["cache_hits"] += 1
        if failure:
            _progress["failures"] += 1
        _progress["input_tokens"] += input_tokens
        _progress["usd"] = _progress["input_tokens"] * PRICE_PER_MTOK_INPUT / 1e6
        n = _progress["n"]
        if n % 20 == 0 or failure:
            print(
                f"[progress] calls={n} cache={_progress['cache_hits']} "
                f"fail={_progress['failures']} tok={_progress['input_tokens']} "
                f"usd≈{_progress['usd']:.5f} model={_progress['resolved_model']}",
                flush=True,
            )
        if _progress["usd"] > 0.25:
            print("STOP: spend > $0.25 — aborting", flush=True)
            raise SystemExit(99)


def make_client():
    from typesafe_sdk import TypeSafeClient, RetryPolicy

    return TypeSafeClient(
        retry=RetryPolicy(
            max_retries=5,
            backoff_initial=0.5,
            backoff_max=30.0,
            http_statuses={408, 429, 500, 502, 503, 504, 529},
            timeout=120.0,
        ),
        timeout=120.0,
    )


def choice_instructions(category: str, category_description: str) -> str:
    # Criterion string appears exactly; category context for the judgment
    return (
        f"The requested contract category is \"{category}\": {category_description}. "
        f"Which of Text A or Text B is {CRITERION}?"
    )


def score_instructions(category: str, category_description: str) -> str:
    return (
        f"The requested contract category is \"{category}\": {category_description}. "
        f"Rate how relevant this contract text is to that category "
        f"(irrelevant / weakly relevant / relevant / highly relevant)."
    )


def truncate(text: str, max_chars: int = 3500) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20] + "\n[...truncated...]"


def load_units() -> dict[str, dict[str, Any]]:
    units = {}
    for line in (ROOT / "data" / "pairs" / "units.jsonl").open():
        d = json.loads(line)
        units[d["unit_id"]] = d
    return units


def load_pairs(strata: set[str] | None = None) -> list[dict[str, Any]]:
    out = []
    for line in (ROOT / "data" / "pairs" / "gold_pairs.jsonl").open():
        d = json.loads(line)
        if strata and d.get("stratum") not in strata:
            continue
        out.append(d)
    return out


def load_queries() -> list[dict[str, Any]]:
    return [json.loads(l) for l in (ROOT / "data" / "pairs" / "candidate_queries.jsonl").open()]


def get_text(unit: dict[str, Any], *, strip: bool) -> str:
    raw = unit.get("text") or ""
    if strip:
        return truncate(strip_meta(raw))
    return truncate(raw)


def call_choice(client, *, text_a: str, text_b: str, instructions: str) -> dict[str, Any]:
    from typesafe_sdk import Choice

    t0 = time.perf_counter()
    response = client.system_one(
        model=MODEL,
        state={"Text A": text_a, "Text B": text_b},
        questions={
            "winner": Choice(
                instructions=instructions,
                criteria={"A": "Text A", "B": "Text B"},
            ),
        },
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    ans = response.answers["winner"]
    usage = response.usage
    return {
        "model": response.model,
        "winner": ans.choice,
        "p_A": float(ans.probabilities.get("A", 0.0)),
        "p_B": float(ans.probabilities.get("B", 0.0)),
        "confidence": float(ans.confidence),
        "probabilities": {k: float(v) for k, v in ans.probabilities.items()},
        "input_tokens": int(usage.input_tokens),
        "output_tokens": int(usage.output_tokens),
        "latency_ms": latency_ms,
    }


def call_score(client, *, text: str, instructions: str) -> dict[str, Any]:
    from typesafe_sdk import Score

    t0 = time.perf_counter()
    response = client.system_one(
        model=MODEL,
        state={"clause": text},
        questions={
            "relevance": Score(
                instructions=instructions,
                criteria=list(SCORE_LEVELS),
            ),
        },
    )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    ans = response.answers["relevance"]
    usage = response.usage
    probs = {str(k): float(v) for k, v in ans.probabilities.items()}
    legend = {str(k): v for k, v in ans.legend.items()}
    return {
        "model": response.model,
        "score": float(ans.score),
        "confidence": float(ans.confidence),
        "probabilities": probs,
        "legend": legend,
        "input_tokens": int(usage.input_tokens),
        "output_tokens": int(usage.output_tokens),
        "latency_ms": latency_ms,
    }


def process_choice_job(
    client,
    *,
    pair: dict[str, Any],
    order: str,
    units: dict[str, dict[str, Any]],
    strip: bool,
    mode: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    ua, ub = units[pair["a"]], units[pair["b"]]
    ta, tb = get_text(ua, strip=strip), get_text(ub, strip=strip)
    if order == "ab":
        display_a, display_b = ta, tb
        id_a, id_b = pair["a"], pair["b"]
    else:
        display_a, display_b = tb, ta
        id_a, id_b = pair["b"], pair["a"]

    ha, hb = text_hash(display_a), text_hash(display_b)
    key = choice_cache_key(MODEL, CRITERION, ha, hb, order, mode)
    instr = choice_instructions(pair["category"], pair["category_description"])

    append_jsonl(
        REQUESTS_PATH,
        {
            "kind": "choice",
            "pair_id": pair["pair_id"],
            "order": order,
            "mode": mode,
            "stratum": pair.get("stratum"),
            "category": pair.get("category"),
            "cache_key": key,
            "n_chars_A": len(display_a),
            "n_chars_B": len(display_b),
        },
    )

    cached = read_cache(key)
    if cached and cached.get("ok"):
        out = dict(cached)
        out["cache_hit"] = True
        rec = {
            "ok": True,
            "kind": "choice",
            "run_id": RUN_ID,
            "pair_id": pair["pair_id"],
            "order": order,
            "mode": mode,
            "stratum": pair.get("stratum"),
            "source": pair.get("source"),
            "gold": pair.get("gold"),
            "category": pair.get("category"),
            "id_A": id_a,
            "id_B": id_b,
            "hash_A": ha,
            "hash_B": hb,
            "winner": out.get("winner"),
            "p_A": out.get("p_A"),
            "p_B": out.get("p_B"),
            "confidence": out.get("confidence"),
            "model": out.get("model"),
            "input_tokens": out.get("input_tokens", 0),
            "output_tokens": out.get("output_tokens", 0),
            "latency_ms": out.get("latency_ms", 0),
            "cache_hit": True,
        }
        append_jsonl(ANSWERS_PATH, rec)
        bump_progress(cache_hit=True, input_tokens=0)
        return out

    if dry_run:
        return {"ok": False, "dry_run": True, "pair_id": pair["pair_id"], "order": order}

    try:
        result = call_choice(client, text_a=display_a, text_b=display_b, instructions=instr)
        with _progress_lock:
            _progress["resolved_model"] = result["model"]
        answer = {
            "ok": True,
            "kind": "choice",
            "run_id": RUN_ID,
            "pair_id": pair["pair_id"],
            "order": order,
            "mode": mode,
            "stratum": pair.get("stratum"),
            "source": pair.get("source"),
            "gold": pair.get("gold"),
            "category": pair.get("category"),
            "id_A": id_a,
            "id_B": id_b,
            "hash_A": ha,
            "hash_B": hb,
            **result,
            "cache_hit": False,
        }
        write_cache(key, {**answer, "ok": True})
        append_jsonl(ANSWERS_PATH, answer)
        append_jsonl(RESPONSES_PATH, {"cache_key": key, **answer})
        bump_progress(input_tokens=result["input_tokens"])
        return answer
    except Exception as e:
        err = {
            "ok": False,
            "kind": "choice",
            "pair_id": pair["pair_id"],
            "order": order,
            "mode": mode,
            "error": repr(e),
        }
        append_jsonl(ANSWERS_PATH, err)
        bump_progress(failure=True)
        return err


def process_score_job(
    client,
    *,
    query: dict[str, Any],
    unit_id: str,
    units: dict[str, dict[str, Any]],
    dry_run: bool = False,
) -> dict[str, Any]:
    unit = units[unit_id]
    text = get_text(unit, strip=True)
    ht = text_hash(text)
    cat = query["category"]
    key = score_cache_key(MODEL, CRITERION, cat, ht)
    instr = score_instructions(cat, query["category_description"])
    is_gold = unit.get("para_id") in set(query.get("gold_para_ids") or []) or unit_id in {
        f"para:{p}" for p in (query.get("gold_para_ids") or [])
    }

    append_jsonl(
        REQUESTS_PATH,
        {
            "kind": "score",
            "query_id": query["query_id"],
            "unit_id": unit_id,
            "category": cat,
            "is_gold": is_gold,
            "cache_key": key,
            "n_chars": len(text),
        },
    )

    cached = read_cache(key)
    if cached and cached.get("ok"):
        out = dict(cached)
        rec = {
            "ok": True,
            "kind": "score",
            "run_id": RUN_ID,
            "query_id": query["query_id"],
            "unit_id": unit_id,
            "para_id": unit.get("para_id"),
            "category": cat,
            "is_gold": is_gold,
            "contract_id": query["contract_id"],
            "score": out.get("score"),
            "confidence": out.get("confidence"),
            "probabilities": out.get("probabilities"),
            "legend": out.get("legend"),
            "model": out.get("model"),
            "input_tokens": out.get("input_tokens", 0),
            "output_tokens": out.get("output_tokens", 0),
            "latency_ms": out.get("latency_ms", 0),
            "cache_hit": True,
            "hash": ht,
        }
        append_jsonl(ANSWERS_PATH, rec)
        bump_progress(cache_hit=True)
        return out

    if dry_run:
        return {"ok": False, "dry_run": True, "query_id": query["query_id"], "unit_id": unit_id}

    try:
        result = call_score(client, text=text, instructions=instr)
        with _progress_lock:
            _progress["resolved_model"] = result["model"]
        answer = {
            "ok": True,
            "kind": "score",
            "run_id": RUN_ID,
            "query_id": query["query_id"],
            "unit_id": unit_id,
            "para_id": unit.get("para_id"),
            "category": cat,
            "is_gold": is_gold,
            "contract_id": query["contract_id"],
            **result,
            "cache_hit": False,
            "hash": ht,
        }
        write_cache(key, {**answer, "ok": True})
        append_jsonl(ANSWERS_PATH, answer)
        append_jsonl(RESPONSES_PATH, {"cache_key": key, **answer})
        bump_progress(input_tokens=result["input_tokens"])
        return answer
    except Exception as e:
        err = {
            "ok": False,
            "kind": "score",
            "query_id": query["query_id"],
            "unit_id": unit_id,
            "error": repr(e),
        }
        append_jsonl(ANSWERS_PATH, err)
        bump_progress(failure=True)
        return err


def run_pool(jobs, client, concurrency: int):
    if not jobs:
        return
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = [ex.submit(fn, client, **kw) for fn, kw in jobs]
        for fut in as_completed(futs):
            fut.result()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--strata", default="A,B", help="comma strata for Choice")
    ap.add_argument("--skip-choice", action="store_true")
    ap.add_argument("--skip-score", action="store_true")
    ap.add_argument("--ablation-names", action="store_true", help="Gate 6: names left in")
    ap.add_argument("--only-ablation", action="store_true")
    args = ap.parse_args()

    ensure_api_key()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    units = load_units()
    strata = {s.strip() for s in args.strata.split(",") if s.strip()}
    pairs = load_pairs(strata)
    queries = load_queries()

    print(
        f"run_id={RUN_ID} criterion={CRITERION!r} model={MODEL} "
        f"pairs={len(pairs)} queries={len(queries)} units={len(units)}",
        flush=True,
    )
    # Document freeze-before-score
    gold_mtime = (ROOT / "data" / "pairs" / "gold_pairs.jsonl").stat().st_mtime
    print(f"gold_pairs mtime={gold_mtime} score_start={time.time()}", flush=True)
    assert time.time() > gold_mtime, "gold must be frozen before score"

    client = None if args.dry_run else make_client()

    jobs = []
    if not args.only_ablation and not args.skip_choice:
        for pair in pairs:
            for order in ("ab", "ba"):
                jobs.append(
                    (
                        process_choice_job,
                        dict(
                            pair=pair,
                            order=order,
                            units=units,
                            strip=True,
                            mode="stripped",
                            dry_run=args.dry_run,
                        ),
                    )
                )

    if not args.only_ablation and not args.skip_score:
        for q in queries:
            for uid in q["candidate_unit_ids"]:
                jobs.append(
                    (
                        process_score_job,
                        dict(query=q, unit_id=uid, units=units, dry_run=args.dry_run),
                    )
                )

    if args.ablation_names or args.only_ablation:
        a_pairs = [p for p in load_pairs({"A"})]
        for pair in a_pairs:
            for order in ("ab", "ba"):
                jobs.append(
                    (
                        process_choice_job,
                        dict(
                            pair=pair,
                            order=order,
                            units=units,
                            strip=False,
                            mode="names_in",
                            dry_run=args.dry_run,
                        ),
                    )
                )

    print(f"jobs={len(jobs)} concurrency={args.concurrency}", flush=True)
    run_pool(jobs, client, args.concurrency)
    print(
        f"DONE calls={_progress['n']} cache={_progress['cache_hits']} "
        f"fail={_progress['failures']} tok={_progress['input_tokens']} "
        f"usd≈{_progress['usd']:.5f} model={_progress['resolved_model']}",
        flush=True,
    )
    (RUN_DIR / "progress_summary.json").write_text(
        json.dumps({**_progress, "run_id": RUN_ID, "criterion": CRITERION}, indent=2)
    )


if __name__ == "__main__":
    main()
