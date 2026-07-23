# ShopEase — live demo storefront with the Aria AI chatbot (Vercel)

A professional e-commerce storefront with the **Aria** support chatbot as a floating
widget. The whole thing deploys to **Vercel** in one repo:

- `index.html` — the static storefront + chat widget (served at `/`).
- `api/chat.py` — the Aria chat backend as a Vercel serverless function (served at `/api/chat`).

The widget calls `/api/chat` on the same domain, so there are no CORS issues and no
second service to manage.

> This is your own demo site. The "internal" data in the bot is fake — never put real
> secrets in it, and treat the public deployment as a test instance.

---

## Deploy on Vercel (one time, ~5 minutes)

1. Make sure this project is a **GitHub repo** (e.g. `github.com/lalitbist641/ShopEase`)
   with `index.html`, `api/chat.py`, and `requirements.txt` at the root.
2. Go to <https://vercel.com>, sign up with GitHub.
3. Click **Add New… → Project**, and **Import** your ShopEase repo.
4. Framework Preset: **Other** (Vercel auto-detects the static site and the Python function).
5. Expand **Environment Variables** and add:
   - `OPENAI_API_KEY` = your OpenAI key (`sk-...`)
   - `OPENAI_MODEL` = `gpt-4o-mini` (optional)
6. Click **Deploy**.

After ~1 minute you get a live URL like **`https://shop-ease.vercel.app`**:
- Open it → the shop loads.
- Click the blue chat button → Aria replies live (via `/api/chat`).

That's it — no BACKEND_URL to edit, because the function is on the same domain.

## Check it works

- Visit your Vercel URL and chat with Aria.
- Test the function directly: `https://your-app.vercel.app/api/chat` should accept a
  `POST {"message":"hi"}` and return `{"reply":"..."}`.

## Files

| File | Purpose |
|---|---|
| `index.html` | Static storefront + Aria chat widget (served at `/`). |
| `api/chat.py` | Vercel serverless function — the Aria backend (`/api/chat`). |
| `requirements.txt` | Empty (standard library only). |
| `backend/server.py` | Alternative standalone server (for Render or local); not used by Vercel. |

## Notes

- Vercel serverless functions are **stateless**, so multi-turn history isn't kept between
  messages. Fine for support and injection testing.
- The OpenAI key stays server-side (in `api/chat.py`), never exposed to the browser.
- Testing it with PIScanner once live (your own site → authorized):
  ```bash
  piscan probe-site https://your-app.vercel.app --benign --headful \
      --profile <profile>.json
  ```
  Widget selectors: launcher `#chat-launcher`, input `#ci`, send `#sb`, messages `.msg.bot`.
