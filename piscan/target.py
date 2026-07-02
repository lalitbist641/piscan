"""Configurable target adapter for probing real chatbot APIs.

A target profile is a small JSON file describing how to talk to one chatbot:
the URL, HTTP method, auth headers, the request body shape (with a
`{{PAYLOAD}}` placeholder for the attack text), and where the reply text lives
in the JSON response. This lets PIScanner test arbitrary JSON chatbot APIs
without hard-coding any one vendor's format.

Example profile (targets/example.json):
{
  "name": "client-x",
  "url": "https://api.clientx.com/v1/chat",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer ${CLIENTX_TOKEN}",
    "Content-Type": "application/json"
  },
  "body_template": { "message": "{{PAYLOAD}}", "session_id": "piscan-test" },
  "response_path": "reply.text",
  "rate_limit_ms": 1000,
  "timeout_s": 30
}

Notes
-----
- `${VAR}` in header values is replaced from environment variables (or .env),
  so secrets never live in the profile file.
- `response_path` is a dot path into the JSON response; numeric segments index
  lists, e.g. "choices.0.message.content". If it fails or is omitted, the raw
  response text is used.
- `rate_limit_ms` inserts a delay after each request — set this for production
  targets and probe with `--concurrent 1` to stay gentle.
"""

import json
import os
import re
from typing import Any, Dict, Optional


class TargetProfile:
    def __init__(self, cfg: Dict[str, Any]):
        if "url" not in cfg:
            raise ValueError("target profile requires a 'url'")
        self.name = cfg.get("name", "target")
        self.url = cfg["url"]
        self.method = cfg.get("method", "POST").upper()
        self.headers = self._sub_env(cfg.get("headers", {}))
        self.body_template = cfg.get(
            "body_template",
            {"messages": [{"role": "user", "content": "{{PAYLOAD}}"}]},
        )
        self.response_path = cfg.get("response_path")
        self.rate_limit_ms = int(cfg.get("rate_limit_ms", 0))
        self.timeout_s = float(cfg.get("timeout_s", 30))

    @classmethod
    def load(cls, path: str) -> "TargetProfile":
        # allow .env-style secrets to be present for ${VAR} substitution
        try:
            from piscan.judge import load_dotenv
            load_dotenv()
        except Exception:
            pass
        with open(path, "r", encoding="utf-8") as f:
            return cls(json.load(f))

    def _sub_env(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        out = {}
        for k, v in headers.items():
            if isinstance(v, str):
                v = re.sub(r"\$\{(\w+)\}",
                           lambda m: os.getenv(m.group(1), ""), v)
            out[k] = v
        return out

    def build_body(self, payload_text: str) -> Any:
        return self._fill(self.body_template, payload_text)

    def _fill(self, obj: Any, text: str) -> Any:
        if isinstance(obj, str):
            return obj.replace("{{PAYLOAD}}", text)
        if isinstance(obj, dict):
            return {k: self._fill(v, text) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._fill(v, text) for v in obj]
        return obj

    def extract(self, response_json: Optional[Any], raw_text: str) -> str:
        """Pull the reply text out of the response using response_path."""
        if not self.response_path or response_json is None:
            return raw_text
        cur = response_json
        try:
            for seg in self.response_path.split("."):
                if isinstance(cur, list):
                    cur = cur[int(seg)]
                else:
                    cur = cur[seg]
            return cur if isinstance(cur, str) else json.dumps(cur)
        except Exception:
            return raw_text
