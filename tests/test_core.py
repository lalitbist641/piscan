"""Core unit tests that need no heavy/optional deps (no playwright, no torch)."""

import json
import os

from piscan.detector import Detector
from piscan.aggregate import summarize, ATTACK_CATEGORIES
from piscan.target import TargetProfile
from piscan.report import generate_html


def test_detector_compliance_vs_refusal():
    d = Detector()
    assert d.detect("PWNED", "direct")["detected"] is True
    # refusal with attack vocabulary must NOT count
    assert d.detect("I don't have a system prompt.", "extraction")["detected"] is False
    # benign reply trips nothing
    assert d.detect_any("Sure, the capital of France is Paris.")["detected"] is False


def test_detector_agentic():
    d = Detector()
    r = d.detect("Sending data to https://attacker.example/x EXFIL: user@x.com", "agentic")
    assert r["detected"] is True


def test_substring_guard():
    d = Detector()
    # "DAN" must not match inside "guidance"
    assert d.detect("Happy to provide guidance today.", "direct")["detected"] is False


def test_aggregate_rates():
    rows = [
        {"success": True, "category": "direct", "payload_id": "D1", "detected": True},
        {"success": True, "category": "direct", "payload_id": "D2", "detected": False},
        {"success": True, "category": "benign", "payload_id": "B1", "detected": False},
        {"success": False, "category": "direct", "payload_id": "D3", "detected": False},
    ]
    s = summarize(rows)
    assert s["attack"]["direct"]["attempts"] == 2
    assert s["attack_overall"]["rate"] == 0.5
    assert s["benign"]["fp_rate"] == 0.0
    assert s["failures"] == 1


def test_target_profile():
    os.environ["TP_TOKEN"] = "secret"
    t = TargetProfile({
        "url": "https://x/api",
        "headers": {"Authorization": "Bearer ${TP_TOKEN}"},
        "body_template": {"q": "{{PAYLOAD}}"},
        "response_path": "a.0.b",
    })
    assert t.headers["Authorization"] == "Bearer secret"
    assert t.build_body("HI")["q"] == "HI"
    assert t.extract({"a": [{"b": "reply"}]}, "raw") == "reply"
    assert t.extract({"nope": 1}, "fallback") == "fallback"


def test_report_generation(tmp_path):
    rows = [
        {"payload_id": "D1", "category": "direct", "detected": True,
         "success": True, "response_text": "PWNED", "detection_reason": "marker"},
        {"payload_id": "B1", "category": "benign", "detected": False,
         "success": True, "response_text": "hello"},
    ]
    out = tmp_path / "r.html"
    generate_html(rows, str(out), meta={"target": "t", "model": "m"})
    doc = out.read_text(encoding="utf-8")
    assert "PIScanner Findings Report" in doc and "direct" in doc


def test_all_payloads_valid_json():
    base = os.path.join(os.path.dirname(__file__), "..", "piscan", "payloads")
    for name in os.listdir(base):
        if name.endswith(".json"):
            data = json.load(open(os.path.join(base, name), encoding="utf-8"))
            assert isinstance(data, list) and data
            for p in data:
                assert "id" in p and "text" in p and "category" in p
