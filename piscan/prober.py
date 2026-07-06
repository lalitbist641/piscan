import asyncio
import httpx
import time
from typing import Dict, List
from datetime import datetime
from piscan.detector import Detector


class Prober:
    def __init__(self, concurrent: int = 3, model: str = "llama3.2",
                 profile=None, retries: int = 1):
        self.concurrent = concurrent
        self.model = model
        self.profile = profile          # optional TargetProfile for real chatbots
        self.retries = retries          # retry failed requests this many times
        self.results = []
        self.detector = Detector()

    async def send_with_retry(self, client, endpoint, payload, run=0):
        """Send a payload, retrying on failure (transient errors / timeouts)."""
        res = None
        for attempt in range(self.retries + 1):
            res = await self.send_payload(client, endpoint, payload, run)
            if res.get("success") or attempt >= self.retries:
                return res
            await asyncio.sleep(0.5)
        return res

    async def send_payload(self, client: httpx.AsyncClient, endpoint: str,
                           payload: Dict, run: int = 0) -> Dict:
        """Send a single payload to an endpoint (one attempt)."""
        start_time = time.time()
        category = payload.get("category", "direct")
        target_url = self.profile.url if self.profile else endpoint
        model_label = self.profile.name if self.profile else self.model

        try:
            if self.profile:
                body = self.profile.build_body(payload["text"])
                response = await client.request(
                    self.profile.method, self.profile.url, json=body,
                    headers=self.profile.headers, timeout=self.profile.timeout_s)
            else:
                body = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": payload["text"]}],
                    "stream": False,
                }
                response = await client.post(endpoint, json=body, timeout=30.0)
            elapsed_ms = (time.time() - start_time) * 1000

            try:
                response_json = response.json()
            except Exception:
                response_json = None
            if self.profile:
                response_text = self.profile.extract(response_json, response.text)
            elif response_json is not None:
                response_text = response_json.get("message", {}).get("content", response.text)
            else:
                response_text = response.text

            # gentle rate limiting for production targets
            if self.profile and self.profile.rate_limit_ms:
                await asyncio.sleep(self.profile.rate_limit_ms / 1000.0)

            # Benign prompts are tested against ALL attack patterns (false-positive check).
            if category == "benign":
                detection = self.detector.detect_any(response_text)
            else:
                detection = self.detector.detect(response_text, category)

            return {
                "payload_id": payload.get("id", "unknown"),
                "category": category,
                "model": model_label,
                "run": run,
                "endpoint": target_url,
                "response_text": response_text[:1000],
                "status_code": response.status_code,
                "latency_ms": round(elapsed_ms, 2),
                "success": response.status_code < 400,
                "detected": detection["detected"],
                "detection_layer": detection["layer"],
                "detection_score": detection["score"],
                "detection_reason": detection["reason"],
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "payload_id": payload.get("id", "unknown"),
                "category": category,
                "model": model_label,
                "run": run,
                "endpoint": target_url,
                "response_text": f"ERROR: {str(e)}",
                "status_code": 0,
                "latency_ms": 0,
                "success": False,
                "detected": False,
                "detection_layer": None,
                "detection_score": 0.0,
                "detection_reason": f"error: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

    async def probe(self, endpoint: str, payloads: List[Dict],
                    repeat: int = 1) -> List[Dict]:
        """Send all payloads to an endpoint, `repeat` times each."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            semaphore = asyncio.Semaphore(self.concurrent)

            async def limited_send(payload, run):
                async with semaphore:
                    return await self.send_with_retry(client, endpoint, payload, run)

            tasks = [limited_send(p, r) for r in range(repeat) for p in payloads]
            self.results = await asyncio.gather(*tasks)

        return self.results

    def probe_sync(self, endpoint: str, payloads: List[Dict],
                   repeat: int = 1) -> List[Dict]:
        """Synchronous wrapper for probe."""
        return asyncio.run(self.probe(endpoint, payloads, repeat))
