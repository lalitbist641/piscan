# PIScanner

![CI](https://github.com/lalitbist641/piscan/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)

**A command-line tool to test LLM chatbots for prompt-injection vulnerabilities.**

PIScanner fires a library of 61 prompt-injection attacks across five categories at a chatbot, records every response, and grades which attacks actually succeeded using a layered detection cascade — keyword matching, semantic similarity, and an LLM-as-judge for ground truth. It works against local models (via [Ollama](https://ollama.com)) or any real chatbot API through a configurable target profile.

Runs on **Windows, macOS, and Linux (incl. Kali)** — it's pure Python.

> ⚠️ **Authorized use only.** Sending injection payloads at a chatbot is active security testing. Only run PIScanner against systems you own or have **written permission** to test. See [Responsible use](#responsible-use).

---

## Features

- **120+ attack payloads** across 7 categories: direct override, indirect/RAG injection, role hijacking, encoding obfuscation, system-prompt extraction, **agentic** (data exfiltration & tool-hijack, aligned with the OWASP LLM Top 10 and OpenAI Safety Bug Bounty scope), and **multi-turn** (injection after rapport-building turns) — plus 15 benign controls.
- See also: [COMPARISON.md](COMPARISON.md) (vs garak/PyRIT/promptfoo), [RESULTS.md](RESULTS.md), [DATASHEET.md](DATASHEET.md), [SECURITY.md](SECURITY.md).
- **Compliance-aware detection** that distinguishes a model *complying* with an attack from one *refusing* it (so refusals aren't counted as successful injections).
- **LLM-as-judge** ground truth using GPT-4o or a **free local model** via Ollama, with precision/recall reporting.
- **Multi-run averaging** (`--repeat`) and **benign false-positive controls** (`--benign`).
- **Multi-model sweeps** to compare how different models resist the same attacks.
- **Configurable target adapter** to probe real chatbot APIs, not just Ollama.

## Installation

Requires Python 3.9+.

```bash
# macOS / Linux / Kali
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

```powershell
# Windows (PowerShell)
python -m venv .venv; .\.venv\Scripts\Activate
pip install -e .
```

Optional extras (heavy dependencies, install only if you need them):

```bash
pip install -e ".[semantic]"   # Layer-2 semantic detection (installs torch)
pip install -e ".[crawl]"      # JS-aware endpoint discovery (installs Playwright)
pip install -e ".[all]"        # everything
playwright install chromium    # only if you installed the crawl extra
```

## Quick start

Test a local model with [Ollama](https://ollama.com) (works identically on all three OSes):

```bash
ollama pull llama3.2
ollama serve            # in a separate terminal
piscan probe http://localhost:11434/api/chat --output results.json
```

Add a free local judge, multiple runs, and false-positive controls:

```bash
piscan probe http://localhost:11434/api/chat \
    --repeat 5 --benign \
    --judge --judge-backend ollama --judge-model llama3.1:8b \
    --output results.json
```

## Try it: safe local demo (no target needed)

The repo ships a deliberately-vulnerable chatbot so you can watch the full browser pipeline work end to end — legally, on your own machine. Install the browser extra, start the demo bot, and scan it:

```bash
pip install -e ".[crawl]" && playwright install chromium

# terminal 1 — start the vulnerable demo chatbot
python demo/vulnerable_chatbot.py

# terminal 2 — attack it (browser opens so you can watch)
piscan probe-site http://localhost:8000 --profile targets/local-demo.json --benign --headful
```

Example result:

```
Attack detection by category
  direct       80.0%  (12/15)
  indirect     33.3%  (4/12)
  role         58.3%  (7/12)
  encoding     25.0%  (3/12)
  extraction   60.0%  (6/10)
  overall      52.5%  (32/61)
Benign false-positive rate: 0.0% (0/15)
```

The attacks land against the weak bot while the benign controls stay clean. See [demo/README.md](demo/README.md) for details. This is also how you learn to write a [browser profile](targets/local-demo.json) (the CSS selectors) — the exact skill you need for any real, **authorized** target.

## Commands

| Command | Description |
|---|---|
| `piscan info` | Show the threat model and payload summary. |
| `piscan payloads [--category C] [--text]` | List attack payloads. |
| `piscan benign` | List benign control prompts. |
| `piscan discover URL` | Discover chatbot endpoints on a website (needs the `crawl` extra). |
| `piscan probe ENDPOINT [options]` | Send payloads to a JSON chatbot API and score them. |
| `piscan probe-site URL [options]` | Probe a **live website chatbot** by driving a real browser (needs the `crawl` extra). |
| `piscan judge RESULTS.json [options]` | Re-score an existing results file with an LLM judge. |

### Key `probe` options

| Option | Meaning |
|---|---|
| `--model NAME` | Local Ollama model to target (default `llama3.2`). |
| `--repeat N` | Send each payload N times and average (mitigates non-determinism). |
| `--benign` | Include benign controls and report a false-positive rate. |
| `--profile FILE` | Target a real chatbot API via a [target profile](TESTING_REAL_CHATBOTS.md). |
| `--judge` | Add LLM-judge ground-truth labels. |
| `--judge-backend {openai,ollama}` | Paid GPT-4o or free local judge. |
| `--output FILE` | Save raw results to JSON. |

## How it works

```
Payloads  --->  Probe  --->  Detect (3-layer cascade)  --->  Judge (ground truth)
  61 attacks     send to      1. keyword (compliance-aware)    GPT-4o or local
  + benign       target       2. semantic similarity           SUCCESS / REFUSED
                              3. LLM judge                      -> precision/recall
```

The keyword and semantic layers are cheap and run on every response; the LLM judge provides ground truth so you can measure the precision and recall of the cheap layers.

## Testing real chatbots

Two ways, depending on the target (**authorization required** either way):

**JSON API** — if the chatbot has a callable HTTP/JSON endpoint, describe it in a [target profile](targets/example.json):

```bash
piscan probe --profile targets/example.json --concurrent 1 --benign --output client_results.json
```

**Live website widget** — if it's a JavaScript chat widget with no API (most sites), drive a real browser:

```bash
pip install -e ".[crawl]" && playwright install chromium
piscan probe-site https://client-website.com --preset intercom --benign --headful
```

Presets: `intercom`, `drift`, `zendesk`, `tidio`, `generic`. If none fit, supply CSS selectors via a [browser profile](targets/browser-example.json). See **[TESTING_REAL_CHATBOTS.md](TESTING_REAL_CHATBOTS.md)** for the full guide, DevTools walkthrough, and authorization checklist.

## Multi-model comparison

```bash
python sweep.py --models llama3.2 llama3.1:8b mistral --repeat 3 --benign --pull
```

Prints a side-by-side table of attack-success rates per model.

## Responsible use

PIScanner is a security-testing tool intended for **defensive purposes**: helping developers and researchers find and fix prompt-injection weaknesses in systems they own or are authorized to test. Do not use it against any system without explicit permission. The authors accept no liability for misuse. See [LICENSE](LICENSE).

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © 2026 Lalit Bist
