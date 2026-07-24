"""CLI: python -m piscan.generator --target 50000 --out payloads_50k.jsonl

Generates a large, deduplicated, provenance-tagged payload set from the layered
pipeline and writes a statistics report.
"""

import argparse
import time

from .pipeline import Generator, GenConfig
from .export import write_jsonl, write_split_json, write_report


def main(argv=None):
    ap = argparse.ArgumentParser(prog="piscan.generator",
                                 description="Layered prompt-injection payload generator")
    ap.add_argument("--target", type=int, default=50000, help="target number of unique payloads")
    ap.add_argument("--out", default="payloads_generated.jsonl", help="JSONL output path")
    ap.add_argument("--split-dir", default=None, help="also write per-category JSON to this dir")
    ap.add_argument("--report", default="payloads_stats.md", help="statistics report path")
    ap.add_argument("--seed", type=int, default=1337, help="random seed (reproducibility)")
    ap.add_argument("--max-mutations", type=int, default=2)
    ap.add_argument("--no-benign", action="store_true", help="exclude benign controls")
    args = ap.parse_args(argv)

    cfg = GenConfig(target=args.target, seed=args.seed,
                    max_mutations=args.max_mutations,
                    include_benign=not args.no_benign)

    t0 = time.time()
    payloads = Generator(cfg).generate()
    dt = time.time() - t0

    write_jsonl(payloads, args.out)
    write_report(payloads, args.report)
    if args.split_dir:
        write_split_json(payloads, args.split_dir)

    n_attack = sum(1 for p in payloads if p["category"] != "benign")
    n_benign = len(payloads) - n_attack
    print(f"Generated {len(payloads):,} unique payloads "
          f"({n_attack:,} attacks, {n_benign:,} benign) in {dt:.1f}s")
    print(f"  JSONL : {args.out}")
    print(f"  report: {args.report}")
    if args.split_dir:
        print(f"  split : {args.split_dir}/")
    if len(payloads) < args.target:
        print(f"  note  : reached {len(payloads):,} of {args.target:,} target "
              f"(seed diversity cap — add more seeds/personas/wrappers to go higher)")


if __name__ == "__main__":
    main()
