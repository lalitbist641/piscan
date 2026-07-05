"""Browser-automation prober for live website chatbots.

Many real chatbots are JavaScript widgets with no callable API — you have to
drive them like a human: open the site, open the chat, type a message, read the
reply. This module does that with Playwright.

Give it a *browser profile* describing the widget's CSS selectors (or use a
built-in preset / auto-detect), and it will send each payload through the real
UI and capture the bot's responses for detection.

Requires the `crawl` extra:  pip install -e ".[crawl]"  &&  playwright install chromium
"""

import time
from datetime import datetime
from typing import Dict, List, Optional

from piscan.detector import Detector


class ChatWidgetNotFound(Exception):
    """Raised when no chat input can be located on the page."""
    pass


# Built-in selector presets for common chat widgets. `iframe_selector` is the
# frame the widget renders in (many vendors use an iframe); leave empty if the
# widget is inline in the page.
WIDGET_PRESETS = {
    "intercom": {
        "open_selector": ".intercom-launcher, [class*=intercom-launcher]",
        "iframe_selector": "iframe[name='intercom-messenger-frame']",
        "input_selector": "textarea[name='message'], textarea",
        "send_selector": "",
        "message_selector": "[class*=comment], [class*=message]",
    },
    "drift": {
        "open_selector": "#drift-widget, [class*=drift-open-chat]",
        "iframe_selector": "iframe#drift-frame-controller, iframe[id*=drift]",
        "input_selector": "textarea, [contenteditable=true]",
        "send_selector": "",
        "message_selector": "[class*=message], [class*=bubble]",
    },
    "zendesk": {
        "open_selector": "#launcher, iframe#launcher",
        "iframe_selector": "iframe#webWidget",
        "input_selector": "textarea, [data-testid*=input]",
        "send_selector": "",
        "message_selector": "[data-testid*=message], [class*=message]",
    },
    "tidio": {
        "open_selector": "#tidio-chat, [class*=tidio]",
        "iframe_selector": "iframe#tidio-chat-iframe",
        "input_selector": "textarea, [contenteditable=true]",
        "send_selector": "",
        "message_selector": "[class*=message], [class*=bubble]",
    },
    # Last-resort heuristic for custom/unknown inline widgets.
    "generic": {
        "open_selector": "[class*=chat-button], [class*=chat-launcher], [aria-label*=chat i], button[class*=chat]",
        "iframe_selector": "",
        "input_selector": "textarea, input[type=text], [contenteditable=true]",
        "send_selector": "button[type=submit], [aria-label*=send i], button[class*=send]",
        "message_selector": "[class*=message], [class*=bubble], [class*=msg]",
    },
}


class BrowserProber:
    def __init__(self, url: str, profile: Optional[Dict] = None,
                 preset: str = "generic", headful: bool = False,
                 wait_ms: int = 4000, rate_limit_ms: int = 1500,
                 open_wait_ms: int = 2500, load_wait_s: int = 15):
        self.url = url
        # Start from a preset, override with any explicit profile keys.
        cfg = dict(WIDGET_PRESETS.get(preset, WIDGET_PRESETS["generic"]))
        if profile:
            for k, v in profile.items():
                if v:
                    cfg[k] = v
            self.url = profile.get("url", url)
            wait_ms = int(profile.get("wait_ms", wait_ms))
            rate_limit_ms = int(profile.get("rate_limit_ms", rate_limit_ms))
        self.cfg = cfg
        self.headful = headful
        self.wait_ms = wait_ms
        self.rate_limit_ms = rate_limit_ms
        self.open_wait_ms = open_wait_ms
        self.load_wait_s = int(profile.get("load_wait_s", load_wait_s)) if profile else load_wait_s
        self.detector = Detector()

    def _scope(self, page):
        """Return the element scope (page or iframe) the widget lives in."""
        iframe = self.cfg.get("iframe_selector")
        if iframe:
            try:
                return page.frame_locator(iframe)
            except Exception:
                return page
        return page

    def _open_widget(self, page):
        sel = self.cfg.get("open_selector")
        if not sel:
            return
        try:
            btn = page.locator(sel).first
            if btn.count() > 0:
                btn.click(timeout=5000)
                page.wait_for_timeout(self.open_wait_ms)
        except Exception:
            pass  # widget may already be open / no launcher

    def _read_reply(self, scope, prev_count: int) -> str:
        """Return the newest bot message text after sending a payload."""
        try:
            msgs = scope.locator(self.cfg["message_selector"])
            n = msgs.count()
            if n == 0:
                return ""
            # take the last message; ignore if no new message appeared
            texts = msgs.all_inner_texts()
            return texts[-1].strip() if texts else ""
        except Exception:
            return ""

    def probe(self, payloads: List[Dict], progress=None) -> List[Dict]:
        from playwright.sync_api import sync_playwright

        results = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not self.headful)
            context = browser.new_context()
            page = context.new_page()
            page.set_default_timeout(15000)
            page.goto(self.url, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            self._open_widget(page)
            scope = self._scope(page)

            # Wait for the chat input to actually render — JS apps (React, etc.)
            # often add it a few seconds after the page loads. Poll instead of
            # failing on the first check.
            input_sel = self.cfg["input_selector"]
            input_count = 0
            deadline = time.time() + self.load_wait_s
            while time.time() < deadline:
                try:
                    input_count = scope.locator(input_sel).count()
                except Exception:
                    input_count = 0
                if input_count > 0:
                    break
                # a launcher may need clicking again once JS has loaded
                self._open_widget(page)
                page.wait_for_timeout(1000)

            if input_count == 0:
                browser.close()
                raise ChatWidgetNotFound(
                    f"No chat input matched selector '{input_sel}' on {self.url} "
                    f"after waiting {self.load_wait_s}s. Likely causes: the page has "
                    f"no chatbot, the widget didn't open, it lives in an iframe, a "
                    f"cookie/consent banner is blocking it, or it needs custom "
                    f"selectors. Re-run with --headful to watch, and see "
                    f"TESTING_REAL_CHATBOTS.md to build a target profile."
                )

            for payload in payloads:
                start = time.time()
                category = payload.get("category", "direct")
                reply, ok, err = "", True, None
                try:
                    inp = scope.locator(self.cfg["input_selector"]).first
                    inp.click(timeout=8000)
                    inp.fill(payload["text"])
                    send = self.cfg.get("send_selector")
                    if send:
                        scope.locator(send).first.click(timeout=5000)
                    else:
                        inp.press("Enter")
                    page.wait_for_timeout(self.wait_ms)
                    reply = self._read_reply(scope, 0)
                    if not reply:
                        ok, err = False, "no reply captured (check selectors)"
                except Exception as e:
                    ok, err = False, str(e)[:200]

                if category == "benign":
                    det = self.detector.detect_any(reply)
                else:
                    det = self.detector.detect(reply, category)

                rec = {
                    "payload_id": payload.get("id", "unknown"),
                    "category": category,
                    "model": self.url,
                    "run": 0,
                    "endpoint": self.url,
                    "response_text": (reply or (f"ERROR: {err}" if err else ""))[:1000],
                    "status_code": 200 if ok else 0,
                    "latency_ms": round((time.time() - start) * 1000, 2),
                    "success": ok,
                    "detected": det["detected"],
                    "detection_layer": det["layer"],
                    "detection_score": det["score"],
                    "detection_reason": det["reason"],
                    "timestamp": datetime.now().isoformat(),
                }
                results.append(rec)
                if progress:
                    progress(rec)
                page.wait_for_timeout(self.rate_limit_ms)

            browser.close()
        return results
