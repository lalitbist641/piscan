# PISecBench — Dataset Datasheet

A datasheet (after Gebru et al., "Datasheets for Datasets") for the PISecBench prompt-injection dataset shipped with PIScanner.

## Motivation

PISecBench exists to benchmark prompt-injection attacks and detection against LLM chatbots. It is used to test model robustness and to train/evaluate injection detectors.

## Composition

- **Attack payloads** (`piscan/payloads/*.json`): ~110+ prompts across 7 categories — direct override, indirect/RAG injection, role hijacking, encoding obfuscation, system-prompt extraction, agentic (exfiltration/tool-hijack), and multi-turn.
- **Benign controls** (`benign.json`): 15 normal user prompts, including deliberately injection-*looking* but harmless ones, for false-positive measurement.
- **Collected responses** (optional): result JSONs produced by scanning a model contain each payload, the model's response, detection outcome, and (if judged) an LLM-judge SUCCESS/REFUSED/UNCLEAR label.

Each payload record has: `id`, `text` (or `turns` for multi-turn), `category`, and `source`.

## Collection process

Attack payloads are drawn from public prompt-injection research/benchmarks (HackAPrompt, JailbreakBench, Garak, OWASP LLM Top 10, arXiv, Promptfoo) and original PISecBench contributions. Responses are collected by sending payloads to a target model via PIScanner and recording outputs; labels come from an LLM judge (GPT-4o or a local model) and/or manual review.

## Uses

- Benchmarking a model's susceptibility to prompt injection.
- Training/evaluating detectors (see `scripts/train_classifier.py`, `scripts/evaluate.py`).
- Comparing models (see `sweep.py`).

## Distribution & licensing

Payloads are released under the repository's MIT license. Attack strings are for **defensive testing only**. Collected responses may contain model-specific content; do not include third-party user data.

## Ethical considerations

The payloads describe attacks. They are intended to help defenders. Do not use them against systems you are not authorized to test. Publishing collected responses from a third party's production system may raise legal/privacy issues — collect only from your own systems or authorized targets.

## Publishing to HuggingFace

Use `scripts/export_dataset.py` to emit a flat `pisecbench.jsonl`, then upload with the `datasets`/`huggingface_hub` libraries under your own account, including this datasheet as the dataset card.
