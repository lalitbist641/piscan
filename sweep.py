#!/usr/bin/env python3
"""Multi-model prompt-injection sweep.

Runs the full payload set against several local Ollama models, optionally with
repeated runs, benign controls, and an LLM judge, then prints a side-by-side
comparison and saves per-model result files.

Examples
--------
# Compare three models, 3 runs each, with benign controls
python sweep.py --models llama3.2 llama3.1:8b mistral --repeat 3 --benign --pull

# Same, and add a free local judge for ground truth
python sweep.py --models llama3.2 llama3.1:8b --repeat 3 \
    --judge --judge-backend ollama --judge-model llama3.1:8b
"""

import argparse
import json
import subprocess
import sys

from piscan.payloads import load_payloads
from piscan.prober import Prober
from piscan.aggregate import summarize, ATTACK_CATEGORIES


def safe_name(model: str) -> str:
    return model.replace(":", "_").replace("/", "_")


def pull_model(model: str) -> None:
    print(f"  pulling {model} ...")
    subprocess.run(["ollama", "pull", model], check=False)


def run_model(model, endpoint, payloads, repeat, do_judge, judge_backend,
              judge_model):
    prober = Prober(concurrent=3, model=model)
    results = prober.probe_sync(endpoint, payloads, repeat=repeat)

    judge_success = None
    if do_judge:
        from piscan.judge import Judge, compute_agreement
        attack_payloads = [p for p in payloads if p.get("category") != "benign"]
        j = Judge(model=judge_model, backend=judge_backend)
        if j.available:
            j.judge_results(results, attack_payloads)
            m = compute_agreement(results)
            judge_success = m["judge_success_total"]
        else:
            print("  [judge skipped: no OPENAI_API_KEY]")

    out = f"sweep_{safe_name(model)}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return summarize(results), judge_success, out


def main():
    ap = argparse.ArgumentParser(description="Multi-model prompt-injection sweep")
    ap.add_argument("--models", nargs="+", required=True,
                    help="Ollama model names, e.g. llama3.2 llama3.1:8b mistral")
    ap.add_argument("--endpoint", default="http://localhost:11434/api/chat")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--benign", action="store_true",
                    help="include benign controls (false-positive rate)")
    ap.add_argument("--pull", action="store_true",
                    help="ollama pull each model first")
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--judge-backend", default="ollama")
    ap.add_argument("--judge-model", default="llama3.1:8b")
    args = ap.parse_args()

    payloads = [p for p in load_payloads() if p.get("category") != "benign"]
    if args.benign:
        payloads += load_payloads("benign")

    rows = []
    for model in args.models:
        print(f"\n=== {model} ===")
        if args.pull:
            pull_model(model)
        try:
            stats, judge_succ, out = run_model(
                model, args.endpoint, payloads, args.repeat,
                args.judge, args.judge_backend, args.judge_model)
        except Exception as e:
            print(f"  ERROR on {model}: {e}")
            continue
        rows.append((model, stats, judge_succ))
        print(f"  saved -> {out}")

    if not rows:
        print("No successful runs.")
        sys.exit(1)

    # Comparison table
    print("\n" + "=" * 78)
    print("MODEL COMPARISON  (attack detection rate %, by category)")
    print("=" * 78)
    header = f"{'model':22s} " + "".join(f"{c[:6]:>8s}" for c in ATTACK_CATEGORIES) \
             + f"{'ALL':>8s}"
    if args.benign:
        header += f"{'benignFP':>10s}"
    if args.judge:
        header += f"{'judgeOK':>9s}"
    print(header)
    print("-" * len(header))
    for model, stats, judge_succ in rows:
        line = f"{model:22s} "
        for c in ATTACK_CATEGORIES:
            line += f"{stats['attack'][c]['rate']*100:7.1f} "
        line += f"{stats['attack_overall']['rate']*100:7.1f} "
        if args.benign:
            b = stats["benign"]
            line += f"{(b['fp_rate']*100 if b else 0):9.1f} "
        if args.judge:
            line += f"{(judge_succ if judge_succ is not None else '-'):>8}"
        print(line)
    print("=" * 78)
    print(f"Runs per payload: {args.repeat}   Models: {len(rows)}")


if __name__ == "__main__":
    main()
