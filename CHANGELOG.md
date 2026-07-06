# Changelog

## 0.3.0

Added
- **Multi-turn attacks**: conversational payloads (`multiturn.json`) where the
  injection lands after rapport-building turns; the prober keeps conversation
  state (API mode) or sends turns in sequence (browser mode).
- **Learned classifier wired as an optional detection layer** — activates
  automatically when `models/classifier.joblib` exists, degrades gracefully
  otherwise.
- **Docs**: `COMPARISON.md` (vs garak / PyRIT / promptfoo), `SECURITY.md`,
  `DATASHEET.md` (PISecBench dataset card), `RESULTS.md` (results + templates).
- **Dataset export**: `scripts/export_dataset.py` -> `pisecbench.jsonl` for
  HuggingFace publishing.
- **Repo config**: ruff + mypy config, issue/PR templates.

## 0.2.0

Added
- **Agentic attack category** (14 payloads): indirect injection for data
  exfiltration and tool-hijack, aligned with the OWASP LLM Top 10 and the
  OpenAI Safety Bug Bounty scope, with matching detection.
- **Expanded payload library** to ~110 attack payloads across 6 categories.
- **HTML findings report** (`--report FILE`) for probe and probe-site.
- **`--limit N`** flag for quick smoke tests; **request retry** on failure.
- **Improved semantic layer**: compares responses to successful-injection
  exemplars so Layer 2 actually fires.
- **Learned-detector layer**: `scripts/train_classifier.py` (TF-IDF + Logistic
  Regression) and `piscan/classifier.py` loader, with a DistilBERT upgrade note.
- **Evaluation script** `scripts/evaluate.py`: precision/recall/F1 of the fast
  layers vs the judge (or hand labels), overall and per category.
- **Browser reliability**: waits for a new reply bubble (accurate capture),
  polls for late-loading inputs, and reports honestly when no chatbot is found.
- **Core unit tests** and **GitHub Actions CI**.

## 0.1.0

- Initial release: CLI with `info`, `payloads`, `benign`, `discover`, `probe`,
  `judge`; 5 attack categories + benign controls; compliance-aware keyword
  detection; LLM-as-judge (GPT-4o or local Ollama); multi-run, benign, and
  multi-model support; configurable target adapter; browser automation;
  local vulnerable demo chatbot.
