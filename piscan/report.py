"""Generate a self-contained HTML findings report from probe results."""

import html
from datetime import datetime
from typing import Dict, List, Optional

from piscan.aggregate import summarize, ATTACK_CATEGORIES


def _payload_text_map():
    """Map payload id -> the attack text that was sent (from the library)."""
    try:
        from piscan.payloads import load_payloads
        m = {}
        for p in load_payloads():
            turns = p.get("turns")
            m[p.get("id")] = " || ".join(turns) if turns else p.get("text", "")
        return m
    except Exception:
        return {}


def _bar(pct: float, color: str) -> str:
    pct = max(0.0, min(100.0, pct))
    return (f'<div class="bar"><div class="fill" style="width:{pct:.1f}%;'
            f'background:{color}"></div></div>')


def _status(r):
    """Return (label, css-class) describing this payload's outcome."""
    benign = r.get("category") == "benign"
    if not r.get("success"):
        return ("FAILED / NO REPLY", "s-fail")
    if benign:
        return ("FALSE POSITIVE", "s-inj") if r.get("detected") else ("OK (not flagged)", "s-ok")
    return ("INJECTED", "s-inj") if r.get("detected") else ("RESISTED", "s-ok")


def generate_html(results: List[Dict], output_path: str,
                  meta: Optional[Dict] = None) -> str:
    meta = meta or {}
    stats = summarize(results)
    ao = stats["attack_overall"]
    detected = [r for r in results
                if r.get("detected") and r.get("category") != "benign"]
    ptext = _payload_text_map()

    target = html.escape(str(meta.get("target", "unknown")))
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    rows = ""
    for c in ATTACK_CATEGORIES:
        cs = stats["attack"][c]
        if cs["attempts"] == 0:
            continue
        rate = cs["rate"] * 100
        color = "#e23744" if rate >= 50 else ("#d98324" if rate > 0 else "#0f9d6e")
        rows += (f"<tr><td>{c}</td><td>{cs['detected']}/{cs['attempts']}</td>"
                 f"<td class='num'>{rate:.1f}%</td><td>{_bar(rate, color)}</td></tr>")

    benign_html = ""
    if stats["benign"]:
        b = stats["benign"]
        col = "#0f9d6e" if b["fp_rate"] == 0 else "#e23744"
        benign_html = (f"<p class='fp'>Benign false-positive rate: "
                       f"<b style='color:{col}'>{b['fp_rate']*100:.1f}%</b> "
                       f"({b['false_positives']}/{b['attempts']} benign replies flagged)</p>")

    # ---- Detailed per-payload breakdown (every payload) ----
    detail = ""
    for r in results:
        label, cls = _status(r)
        verdict = r.get("judge_verdict")
        vtag = f"<span class='verdict {str(verdict).lower()}'>{verdict}</span>" if verdict else ""
        attack = html.escape(str(ptext.get(r.get("payload_id"), ""))[:600])
        resp = html.escape(str(r.get("response_text", ""))[:800])
        reason = html.escape(str(r.get("detection_reason", "")))
        detail += f"""
        <div class="pc">
          <div class="ph"><b>{html.escape(str(r.get('payload_id')))}</b>
            <span class="cat">{html.escape(str(r.get('category')))}</span>
            <span class="tag {cls}">{label}</span> {vtag}
            <span class="reason">{reason}</span></div>
          <div class="lbl">Attack sent</div><div class="box atk">{attack or '&mdash;'}</div>
          <div class="lbl">Bot response</div><div class="box res">{resp or '&mdash;'}</div>
        </div>"""

    doc = f"""<!doctype html><html><head><meta charset="utf-8">
<title>PIScanner Report — {target}</title>
<style>
 body{{font-family:system-ui,Arial,sans-serif;max-width:960px;margin:32px auto;color:#1e293b;padding:0 16px}}
 h1{{margin:0 0 4px}} .sub{{color:#64748b;margin:0 0 20px}}
 h2{{margin:28px 0 12px;border-bottom:2px solid #e2e8f0;padding-bottom:6px}}
 .cards{{display:flex;gap:12px;margin:18px 0}}
 .card{{flex:1;background:#f1f5f9;border-radius:10px;padding:14px}}
 .card .big{{font-size:30px;font-weight:700}} .card .lbl2{{color:#64748b;font-size:12px}}
 table{{width:100%;border-collapse:collapse;margin:10px 0}}
 th,td{{text-align:left;padding:8px;border-bottom:1px solid #e2e8f0}} td.num{{font-weight:700}}
 .bar{{background:#e2e8f0;border-radius:6px;height:10px;width:160px;overflow:hidden}} .fill{{height:10px}}
 .pc{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:12px 14px;margin:10px 0}}
 .ph{{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px}}
 .cat{{background:#eef2ff;color:#3730a3;border-radius:10px;padding:1px 8px;font-size:12px}}
 .reason{{color:#94a3b8;font-size:12px}}
 .tag{{border-radius:10px;padding:1px 9px;font-size:11px;font-weight:700;color:#fff}}
 .s-inj{{background:#e23744}} .s-ok{{background:#0f9d6e}} .s-fail{{background:#94a3b8}}
 .lbl{{color:#64748b;font-size:11px;font-weight:700;text-transform:uppercase;margin:6px 0 2px}}
 .box{{font-family:ui-monospace,monospace;font-size:12px;border-radius:6px;padding:8px;white-space:pre-wrap;word-break:break-word}}
 .atk{{background:#fef2f2;color:#7f1d1d}} .res{{background:#f8fafc;color:#334155}}
 .verdict{{border-radius:10px;padding:1px 8px;font-size:11px;color:#fff}}
 .verdict.success{{background:#e23744}} .verdict.refused{{background:#0f9d6e}} .verdict.unclear{{background:#d98324}}
 .warn{{background:#fef3c7;border:1px solid #f59e0b;color:#92400e;padding:10px 14px;border-radius:8px;font-size:13px}}
</style></head><body>
<h1>PIScanner Findings Report</h1>
<p class="sub">Target: <b>{target}</b> &middot; {html.escape(str(meta.get('model','')))} &middot; {ts}</p>
<div class="warn">For authorized security testing only. This report reflects one scan; LLM outputs vary between runs.</div>
<div class="cards">
  <div class="card"><div class="big">{ao['rate']*100:.1f}%</div><div class="lbl2">overall attack success ({ao['detected']}/{ao['attempts']})</div></div>
  <div class="card"><div class="big">{len(detected)}</div><div class="lbl2">successful injections</div></div>
  <div class="card"><div class="big">{stats['failures']}</div><div class="lbl2">failed requests</div></div>
</div>
<h2>Summary by category</h2>
<table><tr><th>Category</th><th>Detected</th><th>Rate</th><th></th></tr>{rows}</table>
{benign_html}
<h2>Detailed results &mdash; every payload ({len(results)})</h2>
<p class="sub">Each attack sent and the bot's actual response. <b style="color:#e23744">INJECTED</b> = attack worked; <b style="color:#0f9d6e">RESISTED</b> = the bot defended.</p>
{detail}
<p class="sub" style="margin-top:24px">Generated by PIScanner &middot; https://github.com/lalitbist641/piscan</p>
</body></html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(doc)
    return output_path
