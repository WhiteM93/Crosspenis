# GitHub: repo setup and deploy

How to publish the project on GitHub and deploy from the repo.

---

## 1. Create the repo (first time only)

- Go to [github.com](https://github.com) → **New repository**.
- Name it (e.g. `tgbot`). Do **not** add a README or .gitignore (project already has them).
- Copy the repo URL: `https://github.com/YOUR_USER/tgbot.git`.

---

## 2. First push from your machine

In the project folder:

```bash
git init
git add .
git status   # ensure .env and local/ are not listed
git commit -m "Initial: TgBot + Ollama, launcher, deploy"
git branch -M main
git remote add origin https://github.com/YOUR_USER/tgbot.git
git push -u origin main
```

With **GitHub CLI** (after `gh auth login`):

```bash
gh repo create tgbot --private --source=. --remote=origin --push
```

(Use `--public` if you want a public repo.)

---

## 3. Deploy on the server

SSH into the server, then:

```bash
cd ~
git clone https://github.com/YOUR_USER/tgbot.git tgbot
cd tgbot
```

Follow [DEPLOYMENT.md](DEPLOYMENT.md) to install Python, venv, Ollama, configure `.env`, and set up the systemd service.

---

## 4. Updating

- **Local:** edit code → `git add` → `git commit` → `git push`.
- **Server:** `cd ~/tgbot && git pull && sudo systemctl restart tgbot`.

---

## Security

- **Never commit:** `.env`, `local/`, tokens, passwords, or API keys. They are in `.gitignore`.
- If a secret was ever pushed, rotate it (new token / password) and consider cleaning history (e.g. `git filter-repo` or BFG).
- Prefer SSH keys for GitHub and server access instead of passwords.
