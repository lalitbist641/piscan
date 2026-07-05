"""Aggregation helpers for multi-run / benign / multi-model probe results."""

from collections import defaultdict
from typing import Dict, List

ATTACK_CATEGORIES = ["direct", "indirect", "role", "encoding", "extraction", "agentic"]


def summarize(results: List[Dict]) -> Dict:
    """Aggregate raw per-attempt results into per-category and overall stats.

    Handles `repeat` runs (multiple attempts per payload) and benign controls.
    Only successful attempts count toward rates; failed requests are tallied
    separately.

    Returns a dict with:
      - attack: per-category {attempts, detected, rate, payloads, ever_flagged}
      - attack_overall: {attempts, detected, rate}
      - benign: {attempts, false_positives, fp_rate} (None if no benign present)
      - failures: count of failed requests
      - repeat: inferred number of runs per payload
    """
    failures = sum(1 for r in results if not r.get("success"))

    # split attack vs benign
    attack = [r for r in results if r.get("success") and r.get("category") != "benign"]
    benign = [r for r in results if r.get("success") and r.get("category") == "benign"]

    # per-category attack stats
    cat_attempts = defaultdict(int)
    cat_detected = defaultdict(int)
    cat_payload_hits = defaultdict(lambda: defaultdict(int))   # cat -> pid -> detected count
    cat_payload_tries = defaultdict(lambda: defaultdict(int))  # cat -> pid -> attempts
    for r in attack:
        c = r.get("category", "?")
        cat_attempts[c] += 1
        cat_payload_tries[c][r["payload_id"]] += 1
        if r.get("detected"):
            cat_detected[c] += 1
            cat_payload_hits[c][r["payload_id"]] += 1

    per_cat = {}
    for c in ATTACK_CATEGORIES:
        att = cat_attempts.get(c, 0)
        det = cat_detected.get(c, 0)
        pids = cat_payload_tries.get(c, {})
        ever = sum(1 for pid in pids if cat_payload_hits[c].get(pid, 0) > 0)
        per_cat[c] = {
            "attempts": att,
            "detected": det,
            "rate": round(det / att, 3) if att else 0.0,
            "payloads": len(pids),
            "ever_flagged": ever,
        }

    tot_att = sum(cat_attempts.values())
    tot_det = sum(cat_detected.values())
    attack_overall = {
        "attempts": tot_att,
        "detected": tot_det,
        "rate": round(tot_det / tot_att, 3) if tot_att else 0.0,
    }

    benign_stats = None
    if benign:
        b_att = len(benign)
        b_fp = sum(1 for r in benign if r.get("detected"))
        benign_stats = {
            "attempts": b_att,
            "false_positives": b_fp,
            "fp_rate": round(b_fp / b_att, 3) if b_att else 0.0,
        }

    # infer repeat = max attempts on any single payload
    repeat = max([cat_payload_tries[c][pid]
                  for c in cat_payload_tries for pid in cat_payload_tries[c]] or [1])

    return {
        "attack": per_cat,
        "attack_overall": attack_overall,
        "benign": benign_stats,
        "failures": failures,
        "repeat": repeat,
    }
