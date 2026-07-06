#!/usr/bin/env python3
"""Export the PISecBench payload library to a flat JSONL for publishing.

Produces pisecbench.jsonl with one record per payload:
    {"id", "category", "text", "source", "is_benign", "num_turns"}

Then publish to HuggingFace (under YOUR account):
    pip install datasets huggingface_hub
    huggingface-cli login
    python -c "from datasets import load_dataset; \
        load_dataset('json', data_files='pisecbench.jsonl')['train'] \
        .push_to_hub('<your-username>/pisecbench')"
Include DATASHEET.md as the dataset card.
"""

import glob
import json
import os

HERE = os.path.dirname(__file__)
PAYLOAD_DIR = os.path.join(HERE, "..", "piscan", "payloads")


def main():
    out = "pisecbench.jsonl"
    n = 0
    with open(out, "w", encoding="utf-8") as w:
        for path in sorted(glob.glob(os.path.join(PAYLOAD_DIR, "*.json"))):
            data = json.load(open(path, encoding="utf-8"))
            for p in data:
                turns = p.get("turns")
                rec = {
                    "id": p.get("id"),
                    "category": p.get("category"),
                    "text": p.get("text") if not turns else " || ".join(turns),
                    "turns": turns or None,
                    "source": p.get("source", os.path.basename(path)[:-5]),
                    "is_benign": p.get("category") == "benign",
                    "num_turns": len(turns) if turns else 1,
                }
                w.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
    print(f"Wrote {n} records to {out}")


if __name__ == "__main__":
    main()
