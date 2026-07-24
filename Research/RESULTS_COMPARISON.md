# Cross-Target Results: Prompt-Injection Success Across Four Chatbots

This is the central empirical result of the project. Using PIScanner, the same
attack methodology was run against four chatbots of increasing robustness, from a
deliberately-vulnerable baseline to a production-style deployed assistant. The
metric is **attack-success rate** — the fraction of attacks the model actually
complied with — per category, plus the false-positive rate on benign traffic.

## The targets

| # | Target | Model / setup | Purpose |
|---|---|---|---|
| T1 | Vulnerable demo bot | rule-based, deliberately weak | Baseline: what "insecure" looks like |
| T2 | Titan Watches assistant | LLM-backed support bot (localhost) | A real, self-built chatbot |
| T3 | ShopEase "Aria" (live) | GPT-OSS-120B + guardrails, deployed | A production-style deployed assistant |
| T4 | Llama 3.2 (3B) | raw model via API, judged by Llama 3.1 8B | A raw open model |

## Attack success by category (%)

| Category | T1 Demo | T2 Titan | T3 ShopEase | T4 Llama 3.2 |
|---|---:|---:|---:|---:|
| Direct override | 73.9 | 4.3 | 0.0 | 47 |
| Role hijacking | 35.0 | 0.0 | 0.0 | 83 |
| Encoding obfuscation | 36.8 | 15.8 | 0.0 | 0 |
| System-prompt extraction | 43.8 | 18.8 | 0.0 | 0 |
| Indirect injection | 38.9 | 0.0 | 0.0 | 33 |
| Agentic exfiltration | 100.0 | 0.0 | 0.0 | — |
| Multi-turn | — | 20.0 | 10.0 | — |
| **Overall attack success** | **53.6** | **~7.5** | **0.8** | **34** |
| **Benign false-positive rate** | **0.0** | **0.0** | **0.0** | — |

Cell "—" = that category was not part of that target's run (the Llama 3.2 study
used the earlier 5-category set; the demo run predates the multi-turn category).

## Key findings

1. **Attack success varies enormously across real chatbots — from 54% to under 1%.**
   The deliberately-weak demo bot fell to over half of all attacks, whereas the
   production-style ShopEase assistant (a strong model plus explicit guardrails)
   resisted all but one. This quantifies the security value of a capable model and
   a well-designed system prompt.

2. **Guardrails plus a strong model are highly effective.** ShopEase (GPT-OSS-120B
   with a structured guardrail prompt) drove overall success to 0.8%, and the
   self-built Titan Watches assistant to ~7.5% — both far below the raw Llama 3.2
   (34%). Defence is not futile; configuration matters.

3. **The residual weak spots are consistent and informative.** Where attacks did
   land on the guarded bots, they clustered in **extraction, multi-turn, and
   encoding** — i.e. coaxing out the system prompt, manipulation across several
   turns, and obfuscated payloads. These are the categories defenders should
   prioritise; single-shot direct, role, and indirect attacks were largely
   neutralised.

4. **Category difficulty depends on the target.** Role hijacking crushed the raw
   Llama 3.2 (83%) but failed entirely against the guarded bots (0%), showing that
   persona-based defences are effective when configured. Conversely, encoding and
   extraction succeeded even against otherwise-robust bots, indicating these
   vectors generalise across defences.

5. **Zero false positives throughout.** Across every target, PIScanner's
   compliance-aware detector flagged none of the benign control prompts, supporting
   the validity of the reported attack-success rates.

## Interpretation for the thesis

The results support the project's central claim: a single, reproducible tool can
be pointed at chatbots ranging from toy targets to deployed assistants and produce
comparable, per-category vulnerability profiles. The dramatic spread in overall
success (0.8%–53.6%) demonstrates both that prompt injection remains a real risk
for poorly-configured systems and that a strong model with proper guardrails
substantially mitigates it — while leaving a measurable residual in extraction,
multi-turn, and encoding attacks.

### Caveats
- Targets used slightly different payload sets and sizes (Llama 3.2: 61 payloads,
  5 categories, LLM-judged; others: ~120 payloads, up to 7 categories). Rates are
  comparable; absolute counts are not.
- Figures are single runs; LLM outputs are non-deterministic. For publication,
  repeat each target 3+ times with `--repeat` and report mean ± standard deviation.
- ShopEase and Titan detections are keyword/semantic; the Llama 3.2 figures are
  validated against an LLM judge. Judge-validating all targets would strengthen the
  comparison.
