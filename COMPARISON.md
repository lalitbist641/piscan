# How PIScanner compares to other tools

Prompt-injection / LLM red-teaming has several good tools. PIScanner is not trying to replace them; it occupies a specific niche. This page is an honest positioning so you can pick the right tool.

| | **PIScanner** | **garak** | **PyRIT** | **promptfoo** |
|---|---|---|---|---|
| Primary focus | Black-box injection testing of *deployed chatbots* | Broad LLM vulnerability scanner (many probes) | Adversarial/red-team framework (Microsoft) | LLM eval & test harness for developers |
| Targets | Ollama, any JSON chat API, **live website widgets (browser)** | Model/API endpoints | Model/API endpoints, orchestrated attacks | Your own app/prompts |
| Attack categories | 7 (direct, indirect, role, encoding, extraction, agentic, multi-turn) | Dozens of probes | Composable attack strategies | User-defined |
| Success detection | 3-layer cascade: keyword → semantic → **LLM judge** | Per-probe detectors | Scorers (incl. LLM) | Assertions / graders |
| Ground-truth validation | **Judge + precision/recall vs the cheap layers** | Varies | Yes (scorers) | Assertions |
| Live website widgets | **Yes (Playwright)** | No | No | No |
| False-positive controls | **Benign corpus + FP rate** | Partial | Manual | Manual |
| Learner | Optional TF-IDF/DistilBERT classifier | — | — | — |
| Best for | Testing a *specific chatbot* you're authorized to test, end-to-end | Broad automated model scanning | Structured red-team campaigns | CI testing of your own prompts |

## What makes PIScanner different

1. **It tests the deployed product, not just the model.** The browser mode drives a real chat widget the way a user (or attacker) would, so it catches issues in the whole stack, not only the raw API.
2. **Cost-aware detection cascade with judge validation.** Cheap keyword/semantic layers run on everything; an LLM judge sets ground truth so you can *measure* how good the cheap layers are (precision/recall) — most tools don't quantify their own detector.
3. **Explicit false-positive measurement.** Benign controls give a real FP rate, not just a list of "hits."

## When to use something else

- Broad, many-probe scanning of a model → **garak**.
- Orchestrated, multi-strategy red-team campaigns → **PyRIT**.
- Testing *your own* prompts/app in CI → **promptfoo**.

PIScanner pairs well with these: use garak/PyRIT for breadth, PIScanner when you need to test a particular chatbot (including a live web widget) and report precision/recall-validated findings.
