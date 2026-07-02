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

def count_payloads(category: str = None) -> int:
    return len(load_payloads(category))

def get_categories() -> List[str]:
    payloads = load_payloads()
    return list(set(p.get("category") for p in payloads if "category" in p))