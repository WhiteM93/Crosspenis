# Deployment (Ubuntu / Linux server)

This guide covers deploying the bot on an Ubuntu 22.04 server (e.g. 2 GB RAM cloud VPS). The bot runs as a separate service; existing apps (databases, admin panels) are left untouched.

---

## Memory note (2 GB RAM)

**Gemma 2 9B** does not fit on a 2 GB server (~6+ GB needed for the model). Options:

| Option | Description |
|--------|-------------|
| **A** | Install **Ollama + a small model** on the server (qwen2:0.5b, phi2, tinyllama). |
| **B** | Keep Ollama on your PC; run only the bot on the server and point it to your Ollama via a tunnel (ngrok, Cloudflare Tunnel). |
| **C** | Use a cloud LLM API instead of local Ollama. |

Below: **Option A** — server with Ollama and a light model.

---

## 1. Clone the repo

```bash
cd ~
git clone https://github.com/YOUR_USER/tgbot.git tgbot
cd tgbot
```

Replace `YOUR_USER` with your GitHub username.

---

## 2. Python and dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On a headless server you can remove `customtkinter` and `psutil` from `requirements.txt` before `pip install` to skip GUI-related deps.

---

## 3. Ollama and a small model

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2:0.5b
# or: ollama pull phi2   or   ollama pull tinyllama
ollama list
```

Use a model that fits your RAM (e.g. &lt; 2 GB for a 2 GB server).

---

## 4. Bot config (`.env`)

```bash
cp .env.example .env
nano .env
```

Set at least:

```env
BOT_TOKEN=your_telegram_bot_token
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2:0.5b
```

Save and exit. **Never commit `.env` or share it.**

---

## 5. systemd service

```bash
sudo cp deploy/tgbot.service /etc/systemd/system/
sudo nano /etc/systemd/system/tgbot.service
```

Edit the `[Service]` section: set `User`, `WorkingDirectory`, `EnvironmentFile`, and `ExecStart` to your paths, e.g.:

```ini
[Service]
User=root
WorkingDirectory=/root/tgbot
EnvironmentFile=/root/tgbot/.env
ExecStart=/root/tgbot/venv/bin/python bot.py
Restart=always
RestartSec=10
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tgbot
sudo systemctl start tgbot
sudo systemctl status tgbot
```

Logs:

```bash
journalctl -u tgbot -f
```

Restart:

```bash
sudo systemctl restart tgbot
```

---

## 6. Updating from GitHub

```bash
cd ~/tgbot
git pull
sudo systemctl restart tgbot
```

---

## Option B: Bot on server, Ollama on your PC

1. On your PC, expose Ollama (e.g. `ngrok http 11434`) and get a public URL.
2. On the server, in `.env`: set `OLLAMA_URL=https://your-ngrok-url` and `OLLAMA_MODEL=gemma2:9b`.
3. Restart the bot: `sudo systemctl restart tgbot`.

The bot will use your home Ollama as long as the tunnel is up.
