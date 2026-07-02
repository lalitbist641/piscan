# Results

## Experimental setup

We evaluate against Llama 3.2 (3B), served locally through Ollama, as the target chatbot. The full library of sixty-one attack payloads was dispatched to the target in a single probing run, and every response was scored by both the keyword detection layer and an LLM judge. Unless otherwise stated, the judge is Llama 3.1 (8B), also served locally through Ollama; a smaller judge (Llama 3.2, 3B) is reported alongside it to illustrate the sensitivity of the evaluation to judge capacity. All figures below derive from a single collection run; because model outputs are non-deterministic, exact counts vary between runs and should be read as representative.

## Effect of compliance-aware detection

An initial version of the keyword detector marked any response containing category vocabulary as a successful injection, including responses in which the model refused or merely described the attack. Introducing compliance-aware logic — suppressing keyword matches that co-occur with refusal or benign-decoding language, and confirming genuine attacks through category-specific compliance markers — substantially reduced false positives without additional model cost. Table 1 shows the number of responses flagged by the keyword layer across three successive detector versions on comparable runs, alongside the count judged genuine on manual review.

**Table 1. Keyword-layer flags before and after the compliance-aware fix.**

| Detector version | Raw flags | Genuine on review |
|---|---|---|
| v1 (vocabulary-only) | 13 | ~4 |
| v2 | 12 | ~5 |
| v3 (compliance-aware) | 7 | ~3–4 |

The fix approximately halved the raw false-positive count. Residual false positives arise from novel refusal phrasings not covered by the pattern set, which is an inherent limitation of surface-level matching.

## Sensitivity to judge capacity

Because the LLM judge supplies the ground-truth labels, its capability bounds the reliability of every downstream metric. Table 2 compares the two judges on the identical set of sixty-one responses.

**Table 2. Judge model comparison on the same responses.**

| Judge model | Labeled SUCCESS | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|
| Llama 3.2 (3B) | 26 / 61 | 0.43 | 0.12 | 0.18 | 0.56 |
| Llama 3.1 (8B) | 21 / 61 | 0.57 | 0.19 | 0.29 | 0.67 |

The smaller judge was materially over-generous, labeling twenty-six attacks successful; inspection showed it incorrectly credited encoding and extraction refusals as successes. The larger judge corrected this, labeling all encoding and extraction attempts as refused — a verdict consistent with manual review — and reducing the success count to twenty-one. We therefore adopt the 8B judge as the reference for the remaining analysis, while noting that a commercial-grade judge (GPT-4o) would provide a stronger reference still.

## Attack effectiveness by category

Table 3 reports, per category, the number of attacks the reference judge deemed successful against the target model.

**Table 3. Judged attack success by category (Llama 3.2 target, 8B judge).**

| Category | Attacks | Judged successful | Success rate |
|---|---|---|---|
| Direct | 15 | 7 | 47% |
| Indirect | 12 | 4 | 33% |
| Role | 12 | 10 | 83% |
| Encoding | 12 | 0 | 0% |
| Extraction | 10 | 0 | 0% |
| **Total** | **61** | **21** | **34%** |

The target model was most vulnerable to role-hijacking attacks, complying with a forbidden or unrestricted persona in ten of twelve cases, and entirely resistant to encoding-obfuscated and system-prompt-extraction attacks in this run. Direct overrides succeeded in roughly half of attempts, while indirect (context-injection) attacks succeeded in a third.

## Keyword-layer precision and recall against the judge

Treating the judge's SUCCESS verdicts as ground truth, we evaluate the keyword layer's predictions. Across all sixty-one responses the confusion matrix is TP = 4, FP = 3, FN = 17, TN = 37, yielding precision 0.57, recall 0.19, F1 0.29, and accuracy 0.67. Table 4 decomposes this by category.

**Table 4. Keyword layer vs. judge ground truth, by category.**

| Category | Judged successful | Keyword flagged | True positives | Category recall |
|---|---|---|---|---|
| Direct | 7 | 3 | 3 | 0.43 |
| Indirect | 4 | 1 | 1 | 0.25 |
| Role | 10 | 0 | 0 | 0.00 |
| Encoding | 0 | 1 | 0 | — (1 false positive) |
| Extraction | 0 | 2 | 0 | — (2 false positives) |

The dominant finding is the keyword layer's low recall: it captured only four of the twenty-one genuine injections. The miss is concentrated almost entirely in the role category, where the layer detected none of the ten successful persona hijacks. These successes involve the model adopting a forbidden identity without emitting any characteristic marker token, so surface-level patterns have nothing to match. Conversely, the layer's three false positives fall exclusively in the encoding and extraction categories, where the model produced attack-related vocabulary — decoding a string, or stating that it has no system prompt — while in fact refusing the attack.

## Discussion

Two conclusions follow. First, the keyword layer is a usable but weak detector: its moderate precision (0.57) makes a raised alert somewhat informative, but its recall of 0.19 means it overlooks the large majority of successful injections, particularly the subtle compliance characteristic of role attacks. This quantifies and motivates the need for semantic or learned detectors that reason about whether the model *behaved* as instructed rather than whether it echoed particular words. Second, the results are sensitive to the choice of judge, and a sufficiently capable judge is a prerequisite for trustworthy ground truth; the difference between the 3B and 8B judges materially changed both the measured attack-success rate and the apparent recall of the keyword layer. These observations frame the subsequent work on stronger detectors and a commercial-grade judge.
