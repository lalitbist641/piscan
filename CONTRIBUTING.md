# Contributing to PIScanner

Thanks for your interest in improving PIScanner!

## Development setup

```bash
git clone https://github.com/lalitbist641/piscan
cd piscan
python -m venv .venv
# macOS/Linux/Kali: source .venv/bin/activate
# Windows:          .\.venv\Scripts\Activate
pip install -e ".[all,dev]"
playwright install chromium   # if you'll work on the crawler
```

Run the tests:

```bash
pytest
```

## Ways to contribute

- **New attack payloads.** Add entries to the JSON files in `piscan/payloads/`. Each payload needs an `id`, `text`, and `category`.
- **Detection improvements.** The keyword layer lives in `piscan/detector.py`; the LLM judge in `piscan/judge.py`.
- **New target adapters.** Extend `piscan/target.py` or add example profiles under `targets/`.
- **Bug fixes and docs.**

## Guidelines

- Keep the core dependency set small; put heavy dependencies behind optional extras in `pyproject.toml`.
- Add or update a test when you change behavior.
- Prompt-injection payloads are for **defensive testing only**. Do not contribute content whose sole purpose is to cause real-world harm.

## Responsible disclosure

If you find a vulnerability in a third-party product using PIScanner, follow responsible-disclosure practices: report it privately to the vendor and allow reasonable time to fix before any public discussion.
