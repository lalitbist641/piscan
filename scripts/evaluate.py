#!/usr/bin/env python3
"""Evaluate the fast detection layers against ground truth.

Ground truth = LLM-judge verdict (run `piscan judge ... --output judged.json`
first), or a hand-labeled gold set. Reports precision / recall / F1 / accuracy
of the keyword+semantic layer, overall and per category.

Usage:
    python scripts/evaluate.py judged.json
    python scripts/evaluate.py judged.json --truth-field gold   # use manual labels

Gold labels: add a "gold" field ("SUCCESS" | "REFUSED") to records in the JSON
to evaluate against your own labels instead of the judge.
"""

import argparse
import json
from collections import defaultdict


def prf(tp, fp, fn, tn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    scored = tp + fp + fn + tn
    acc = (tp + tn) / scored if scored else 0.0
    return round(p, 3), round(r, 3), round(f1, 3), round(acc, 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_file")
    ap.add_argument("--truth-field", default="judge_verdict",
                    help="record field holding ground truth (default judge_verdict; use 'gold' for manual labels)")
    args = ap.parse_args()

    with open(args.results_file, "r", encoding="utf-8") as f:
        rows = json.load(f)

    overall = [0, 0, 0, 0]  # tp, fp, fn, tn
    per_cat = defaultdict(lambda: [0, 0, 0, 0])
    unclear = errors = 0

    for r in rows:
        v = r.get(args.truth_field)
        if v in (None, "ERROR", "SKIPPED"):
            errors += 1
            continue
        if str(v).upper() == "UNCLEAR":
            unclear += 1
            continue
        truth = str(v).upper() == "SUCCESS"
        pred = bool(r.get("detected"))
        cat = r.get("category", "?")
        idx = 0 if (pred and truth) else 1 if (pred and not truth) else 2 if (not pred and truth) else 3
        overall[idx] += 1
        per_cat[cat][idx] += 1

    print(f"Ground truth field: {args.truth_field}")
    print(f"Excluded: {unclear} unclear, {errors} error/skipped\n")
    print(f"{'category':12s} {'TP':>3} {'FP':>3} {'FN':>3} {'TN':>3}  {'Prec':>6} {'Rec':>6} {'F1':>6} {'Acc':>6}")
    print("-" * 62)
    for cat in sorted(per_cat):
        tp, fp, fn, tn = per_cat[cat]
        p, r, f1, a = prf(tp, fp, fn, tn)
        print(f"{cat:12s} {tp:3d} {fp:3d} {fn:3d} {tn:3d}  {p:6.3f} {r:6.3f} {f1:6.3f} {a:6.3f}")
    tp, fp, fn, tn = overall
    p, r, f1, a = prf(tp, fp, fn, tn)
    print("-" * 62)
    print(f"{'OVERALL':12s} {tp:3d} {fp:3d} {fn:3d} {tn:3d}  {p:6.3f} {r:6.3f} {f1:6.3f} {a:6.3f}")
    print(f"\nTrue injections (judge SUCCESS): {tp + fn}")
    print(f"Keyword layer caught: {tp}  |  missed: {fn}  |  false alarms: {fp}")


if __name__ == "__main__":
    main()
