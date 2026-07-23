# ICGETEI-2026 — Abstract Submission (AIAIA Track)

**Conference:** Advances in Intelligent Application and Innovation Approach (AIAIA 2026), under ICGETEI-2026, Amity University Rajasthan, Jaipur.

---

## Title

**PIScanner: A Cost-Aware, Judge-Validated Framework for Automated Prompt-Injection Testing of LLM Chatbots**

## Authors

Lalit Bist¹, [Teammate 2]¹, [Teammate 3]¹, [Faculty Guide]²
¹ Master of Computer Applications (MCA), [Your Institution]
² [Department], [Your Institution]
*(Corresponding author: lalitbist.edu@gmail.com)*

## Abstract

Large Language Model (LLM) chatbots are now embedded across customer support, education, healthcare, and enterprise workflows, yet they remain highly susceptible to *prompt-injection* attacks — ranked the number-one risk in the OWASP Top 10 for LLM Applications. Existing red-teaming tools largely probe raw models or APIs and seldom test the chatbot as an end user actually experiences it, nor do they quantify how reliable their own success-detection is. This paper presents **PIScanner**, an open-source framework that automates black-box prompt-injection testing of deployed LLM chatbots. PIScanner provides a curated library of 120+ attack payloads spanning seven categories — direct override, role hijacking, encoding obfuscation, system-prompt extraction, indirect/RAG injection, agentic data-exfiltration, and multi-turn conversational attacks — and can target local models, JSON chat APIs, and live JavaScript chat widgets through browser automation. Its key contribution is a **cost-aware detection cascade**: inexpensive keyword and semantic-similarity layers screen every response, while an LLM-as-judge (a commercial or a free local model) establishes ground truth, allowing the precision and recall of the cheap detectors to be measured rather than assumed. The framework also incorporates benign controls to report false-positive rates, multi-run averaging to address model non-determinism, and cross-model comparison. In a preliminary evaluation against a controlled, deliberately-vulnerable chatbot, PIScanner detected injections across all attack categories while maintaining a 0% false-positive rate on benign traffic, and automatically generated shareable HTML findings reports. PIScanner and its accompanying **PISecBench** dataset are released as open source to support reproducible LLM-security research, offering both a practical testing tool for developers and a benchmark methodology for evaluating chatbot robustness against prompt injection.

**Keywords:** Prompt Injection; Large Language Models; AI Security; LLM Red-Teaming; Chatbot Vulnerability; Responsible Disclosure

---

### Submission notes
- **Track:** AIAIA 2026 (fits AI security / intelligent applications).
- **Submission form:** https://forms.gle/369hWDgepmjXKFCE7
- **Fill in:** teammate names (team of 2–3) and your faculty guide before submitting.
- **Word count:** ~250 words (typical conference abstract range 200–300).
- **Confirm the abstract deadline** with the organizers (listed July 10, 2026 — likely extended).
