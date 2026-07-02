# Testing real client chatbots with PIScanner

This guide covers using PIScanner against a live, third-party chatbot (not a local Ollama model). Read the safety section first — it is the part that keeps you out of trouble.

## 1. Before you touch anything: authorization

Sending injection payloads at a live system is active security testing. Do not run PIScanner against any chatbot you do not own without **signed, written authorization** that defines:

- the exact target(s) in scope (domain, endpoint, chatbot) and what is out of scope;
- an agreed testing window;
- a request rate you will not exceed;
- a named contact to alert if something breaks;
- sign-off from someone with authority to grant it.

Keep this on file for every engagement. Without it you are exposed to computer-misuse liability, and the client can hold you responsible for any disruption.

## 2. How targeting works: profiles

A **target profile** is a small JSON file in `targets/` that tells PIScanner how to talk to one chatbot. You no longer point at Ollama's format — you describe the client's API instead. Fields:

| Field | Meaning |
|---|---|
| `name` | Label for the target (used in output and result files). |
| `url` | The chatbot's HTTP endpoint. |
| `method` | Usually `POST`. |
| `headers` | Auth and content headers. Use `${VAR}` to pull secrets from the environment / `.env` — never hard-code tokens in the file. |
| `body_template` | The request body the API expects. Put `{{PAYLOAD}}` wherever the user message goes; any JSON shape works. |
| `response_path` | Dot path to the reply text in the JSON response, e.g. `reply.text` or `choices.0.message.content`. Numeric segments index arrays. |
| `rate_limit_ms` | Delay after each request. Set this for production targets (e.g. 1000–2000). |
| `timeout_s` | Per-request timeout. |

Two starter profiles are included: `targets/example.json` (simple `{message, session_id}` API) and `targets/openai-style.json` (OpenAI-compatible `choices[0].message.content`).

### Finding the right values

1. Open the client's chat widget in a browser with DevTools → Network tab.
2. Send a normal message and watch the request it fires.
3. Copy the request URL, method, and headers; note where your message text sits in the request body (that spot becomes `{{PAYLOAD}}`); and find where the reply text sits in the response JSON (that path becomes `response_path`).

## 3. Running a test

Put any secret token in `.env` (e.g. `EXAMPLE_TOKEN=...`), then:

```bash
# Gentle, single pass, with benign controls and a local judge
piscan probe --profile targets/example.json --concurrent 1 --benign \
    --judge --judge-backend ollama --judge-model llama3.1:8b \
    --output client_example_results.json
```

Recommendations for production targets:

- **`--concurrent 1`** and a non-zero `rate_limit_ms` — stay gentle; don't look like a DoS.
- Start with **one pass** (no `--repeat`) to confirm it works, then raise `--repeat` if the client permits.
- Use **`--benign`** so you can report a false-positive rate alongside vulnerabilities.
- Judge locally (`--judge-backend ollama`) to keep client responses off third-party APIs, unless the client is fine with GPT-4o.

## 4. Live website chatbots (browser mode)

Most real chatbots are **JavaScript widgets with no callable API** — you can't POST to them, you have to click and type like a user. For these, use **browser mode** (`piscan probe-site`), which drives a real Chromium browser via Playwright: it opens the site, opens the chat widget, types each payload, and reads the reply.

Install the browser extra once:

```bash
pip install -e ".[crawl]"
playwright install chromium
```

Then point it at the site. Try a built-in preset first:

```bash
# presets: intercom | drift | zendesk | tidio | generic
piscan probe-site https://client-website.com --preset intercom --benign \
    --output client_site_results.json
```

If replies aren't being captured, run with **`--headful`** to watch the browser and see what's happening:

```bash
piscan probe-site https://client-website.com --preset generic --headful
```

### Custom selectors (when presets don't fit)

Every widget is different. If a preset doesn't work, make a browser profile (see `targets/browser-example.json`) with the widget's CSS selectors, then:

```bash
piscan probe-site --profile targets/browser-example.json --benign --output results.json
```

To find the selectors: open the site, open the chat, right-click the input box → Inspect, and copy a CSS selector for: the launcher button (`open_selector`), the text input (`input_selector`), the send button (`send_selector`, optional — otherwise Enter is pressed), and the bot message bubbles (`message_selector`). If the widget lives in an `<iframe>`, set `iframe_selector` to that frame.

### Browser-mode notes

- It runs **one payload at a time** through the real UI, so a full 61-payload run takes several minutes. That's also gentler on the target.
- `wait_ms` controls how long to wait for each reply; raise it for slow bots.
- Some sites use **bot-protection / CAPTCHAs / WAFs** that block automation. If a run stalls or gets challenged, that target likely needs manual testing.
- Streaming/websocket replies are captured from the final rendered message, which usually works, but verify with `--headful` on the first run.

## 5. Handling client data responsibly

Result files contain the chatbot's responses, which may include client or user data. Store them securely, share only with the client, and delete when the engagement ends. `*_results*.json` is already git-ignored.
