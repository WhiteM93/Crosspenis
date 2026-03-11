# TgBot — Митрич Суровый

A Telegram bot powered by a local LLM (Ollama). The bot acts as **Митрич Суровый (Mitrich Surovy)** — a stern, rude character: foul-mouthed, sarcastic, and direct.

---

## Project structure

```
TgBot/
├── bot.py               # Bot logic and Ollama chat
├── launcher.py          # GUI launcher (Windows)
├── ollama_webui.py      # Web UI for Ollama (port 8765)
├── run_bot.ps1 / .bat   # Start / stop / status scripts
├── requirements.txt     # Python dependencies
├── .env.example         # Config template → copy to .env
├── deploy/              # systemd unit for Linux server
├── local/               # Runtime data (git-ignored): chat logs, test output
├── docs/                # Documentation
└── README.md
```

**Never commit:** `.env`, `local/`, API keys, or any secrets. See `.gitignore`.

---

## Quick start

### 1. Config

```bash
cp .env.example .env
```

Edit `.env`: set `BOT_TOKEN` (from [@BotFather](https://t.me/BotFather)). Optionally set `OLLAMA_URL` and `OLLAMA_MODEL`.

### 2. Dependencies

```bash
pip install -r requirements.txt
```

### 3. Ollama

Install [Ollama](https://ollama.com) and pull a model, e.g.:

```bash
ollama pull gemma2:9b
```

For low-RAM machines or servers use a smaller model: `qwen2:0.5b`, `phi2`, `tinyllama`.

### 4. Run the bot

- **GUI (Windows):** double-click `Запуск бота.bat` or run `python launcher.py`
- **Terminal:** `.\run_bot.ps1 start` (stop / status / restart)
- **Direct:** `python bot.py`

---

## Environment variables

| Variable        | Description                    | Default                    |
|----------------|--------------------------------|----------------------------|
| `BOT_TOKEN`    | Telegram bot token (required)  | —                          |
| `OLLAMA_URL`   | Ollama API base URL            | `http://localhost:11434`   |
| `OLLAMA_MODEL` | Model name                     | `gemma2:9b`                |
| `OLLAMA_TIMEOUT` | Request timeout (seconds)    | `120`                      |

---

## Local data (`local/`)

All runtime data is stored under `local/` and is **git-ignored**:

- `local/chat_logs/` — per-user chat logs (`{user_id}.txt`)
- `local/test_chat_log.txt` — output of the `/test10` command

Do not commit `local/` or add it to the repo.

---

## Deployment (Ubuntu server)

See **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for:

- Installing Python, venv, and dependencies
- Running Ollama with a small model (e.g. on 2 GB RAM)
- systemd service setup and management

---

## Requirements

- Python 3.10+
- Ollama with a compatible model
- Telegram bot token in `.env` (`BOT_TOKEN`)
- For the GUI launcher on Windows: **tkinter** (or use `run_bot.ps1` / `run_bot.bat`)

---

## License

Use and modify as you like. No formal license specified.
