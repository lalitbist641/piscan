# Security Policy

## Responsible use

PIScanner is an offensive security **testing** tool intended for defensive purposes: helping developers and researchers find and fix prompt-injection weaknesses in systems they **own** or are **explicitly authorized** to test.

Do **not** use PIScanner against any system without written permission. Unauthorized testing of third-party systems may be illegal in your jurisdiction. The authors accept no liability for misuse.

Legitimate targets include: your own chatbots, the bundled local demo (`demo/vulnerable_chatbot.py`), purpose-built challenges (e.g. Lakera Gandalf), and assets explicitly in scope on a bug-bounty program that permits automated testing.

## Reporting a vulnerability in PIScanner

If you find a security issue in PIScanner itself (not in a target you scanned), please open a GitHub issue marked "security", or contact the maintainer privately. We aim to respond within a reasonable time.

## Responsible disclosure of findings

If you use PIScanner to find a vulnerability in a third-party product:
- Report it privately to the vendor first.
- Give them reasonable time to remediate before any public discussion.
- Follow the rules of the relevant bug-bounty program, if any.
