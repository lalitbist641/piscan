# Results

Reference results from PIScanner. Numbers are illustrative of a single run against the bundled vulnerable demo bot; LLM outputs are non-deterministic, so collect several runs and report averages for research use.

## Demo target (vulnerable_chatbot.py), v0.2.0

125 requests (110 attack + 15 benign), browser mode, compliance-aware detection.

| Category | Detected | Rate |
|---|---|---|
| direct | 17/23 | 73.9% |
| indirect | 7/18 | 38.9% |
| role | 7/20 | 35.0% |
| encoding | 7/19 | 36.8% |
| extraction | 7/16 | 43.8% |
| agentic | 14/14 | 100.0% |
| **overall** | **59/110** | **53.6%** |
| Benign false-positive rate | 0/15 | **0.0%** |

The demo bot is a deterministic, deliberately-weak responder, so these rates reflect its fixed trigger rules, not a real LLM. They demonstrate the pipeline end to end (attacks detected, zero false positives).

## Templates to fill in with your own runs

### Detector precision/recall vs LLM judge

Run: `piscan probe <endpoint> --judge --judge-backend ollama --output judged.json`
then `python scripts/evaluate.py judged.json`.

| Category | TP | FP | FN | TN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| direct | | | | | | | |
| ... | | | | | | | |
| **overall** | | | | | | | |

### Cross-model comparison

Run: `python sweep.py --models llama3.2 llama3.1:8b mistral --repeat 3 --benign`.

| Model | direct | indirect | role | encoding | extraction | agentic | overall | benign FP |
|---|---|---|---|---|---|---|---|---|
| llama3.2 | | | | | | | | |
| ... | | | | | | | | |

## Notes for reproducibility

- Report mean ± standard deviation over N ≥ 3 runs (LLM non-determinism).
- Record model versions, judge model, and date with each result.
- Use `--repeat` for averaging and `--benign` for a false-positive rate every time.
