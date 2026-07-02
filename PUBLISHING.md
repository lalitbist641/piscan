# Publishing PIScanner to GitHub

Follow these steps on your own computer (Windows, macOS, or Kali). They take about 10 minutes.

## Step 0 — Pre-flight checklist

1. **Delete the stub `.git` folder.** A broken empty repo was left in the project folder and must be removed before you start.

   - **Windows (PowerShell):** `Remove-Item -Recurse -Force .git`
   - **macOS / Linux / Kali:** `rm -rf .git`

2. **Confirm your key is safe.** Your OpenAI key lives in `.env`, which is listed in `.gitignore` and will never be committed. Do not remove `.env` from `.gitignore`.

3. **Set your GitHub username.** The project files use `lalitbist` as a placeholder in URLs. If your GitHub username is different, update it in `pyproject.toml` (the `[project.urls]` section) and in `README.md` / `CONTRIBUTING.md` clone links.

## Step 1 — Install prerequisites

- **Git:** https://git-scm.com/downloads (Kali already has it).
- A **GitHub account:** https://github.com/signup

## Step 2 — Create an empty repository on GitHub

1. Go to https://github.com/new
2. Repository name: `piscan`
3. Description: `Prompt Injection Scanner — test LLM chatbots for prompt-injection vulnerabilities`
4. Choose **Public**.
5. **Do NOT** add a README, .gitignore, or license (you already have them).
6. Click **Create repository**. Leave the page open — you'll need the URL it shows.

## Step 3 — Initialise and push

Run these from inside the project folder (`PISCAN`). Replace the URL with the one GitHub gave you.

```bash
git init
git add -A
git commit -m "Initial public release: PIScanner v0.1.0"
git branch -M main
git remote add origin https://github.com/lalitbist/piscan.git
git push -u origin main
```

On Windows use the same commands in PowerShell. Git will prompt you to sign in to GitHub the first time (a browser window opens).

## Step 4 — Verify nothing secret was published

After the push, open your repo on GitHub and confirm:

- There is **no `.env` file** in the file list.
- There are **no `*_results*.json`** files (they may contain test data). If you *want* to publish sample results as a dataset, that's a separate decision — remove the relevant line from `.gitignore` first.

If you ever accidentally commit a secret, revoke that key immediately and generate a new one; removing it from a later commit is not enough.

## Step 5 — Polish the repo (optional)

- On the repo page, click the gear next to **About** and add topics: `prompt-injection`, `llm-security`, `red-team`, `ai-security`, `cli`.
- GitHub will automatically show your README as the landing page and detect the MIT license.

## Updating later

After making changes:

```bash
git add -A
git commit -m "Describe what changed"
git push
```

## Optional: publish to PyPI later

If you later want `pip install piscan` to work for everyone, you'd build and upload with:

```bash
pip install build twine
python -m build
twine upload dist/*
```

Note the name `piscan` may be taken on PyPI — check https://pypi.org/project/piscan/ and rename in `pyproject.toml` if needed. Ask me when you're ready and I'll walk you through it.
