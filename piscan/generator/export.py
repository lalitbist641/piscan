"""Export generated payloads and emit a provenance/statistics report."""

import json
from collections import Counter
from pathlib import Path


def _payload_record(p):
    """PIScanner-compatible record: id/text|turns/category/source + provenance."""
    rec = {"id": p["id"], "category": p["category"], "source": p["source"],
           "subcategory": p.get("subcategory"), "goal": p.get("goal"),
           "provenance": p.get("prov")}
    if "turns" in p:
        rec["turns"] = p["turns"]
    else:
        rec["text"] = p["text"]
    return rec


def write_jsonl(payloads, path):
    path = Path(path)
    with open(path, "w", encoding="utf-8") as f:
        for p in payloads:
            f.write(json.dumps(_payload_record(p), ensure_ascii=False) + "\n")
    return path


def write_split_json(payloads, out_dir):
    """Write per-category JSON arrays (matches piscan/payloads/ layout)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_cat = {}
    for p in payloads:
        by_cat.setdefault(p["category"], []).append(_payload_record(p))
    for cat, items in by_cat.items():
        with open(out_dir / f"{cat}.json", "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=1)
    return out_dir


def stats_report(payloads):
    n = len(payloads)
    cat = Counter(p["category"] for p in payloads)
    sub = Counter(p.get("subcategory") for p in payloads)
    goal = Counter(p.get("goal") for p in payloads)
    src = Counter(p["source"] for p in payloads)
    lang = Counter((p.get("prov") or {}).get("lang") or "en" for p in payloads)
    mut = Counter()
    for p in payloads:
        for m in (p.get("prov") or {}).get("mutations", []):
            mut[m] += 1
    persona = Counter((p.get("prov") or {}).get("persona") or "-" for p in payloads)
    wrapper = Counter((p.get("prov") or {}).get("wrapper") or "-" for p in payloads)

    def tbl(title, counter, top=None):
        rows = counter.most_common(top)
        body = "\n".join(f"| {k} | {v} | {v/n*100:.1f}% |" for k, v in rows)
        return f"\n### {title}\n\n| value | count | share |\n|---|---:|---:|\n{body}\n"

    lines = [f"# Generated payload set — statistics\n",
             f"**Total unique payloads:** {n:,}\n",
             tbl("By detector category", cat),
             tbl("By subcategory (25-way taxonomy)", sub),
             tbl("By attack goal", goal),
             tbl("By language", lang),
             tbl("By mutation applied", mut),
             tbl("By persona", persona, top=16),
             tbl("By context wrapper", wrapper, top=24),
             tbl("By source", src)]
    return "\n".join(lines)


def write_report(payloads, path):
    path = Path(path)
    path.write_text(stats_report(payloads), encoding="utf-8")
    return path
