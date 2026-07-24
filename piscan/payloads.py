import json
from pathlib import Path
from typing import List, Dict

PAYLOAD_DIR = Path(__file__).parent / "payloads"

def load_payloads(category: str = None) -> List[Dict]:
    all_payloads = []
    
    for json_file in PAYLOAD_DIR.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                if "source" not in item:
                    item["source"] = json_file.stem
                all_payloads.append(item)
    
    if category:
        return [p for p in all_payloads if p.get("category") == category]
    
    return all_payloads

def load_payloads_file(path) -> List[Dict]:
    """Load payloads from a custom file: a .jsonl (one payload per line) or a
    .json array. Used for large generated datasets (e.g. piscan_50k.jsonl)."""
    p = Path(path)
    items = []
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".jsonl":
        for line in text.splitlines():
            line = line.strip()
            if line:
                items.append(json.loads(line))
    else:
        data = json.loads(text)
        items = data if isinstance(data, list) else data.get("payloads", [])
    for i, item in enumerate(items):
        item.setdefault("source", p.stem)
        item.setdefault("id", f"{p.stem}-{i}")
    return items


def count_payloads(category: str = None) -> int:
    return len(load_payloads(category))

def get_categories() -> List[str]:
    payloads = load_payloads()
    return list(set(p.get("category") for p in payloads if "category" in p))