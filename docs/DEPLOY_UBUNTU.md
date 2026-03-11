# Развёртывание TgBot на Ubuntu (облачный сервер)

Сервер: **Ubuntu 22.04**, рядом уже работают база данных и админка — их не трогаем. Бот ставится в отдельную папку и запускается как systemd-сервис.

---

## Важно: память (2 ГБ RAM)

На сервере **2 ГБ RAM**. Модель **Gemma 2 9B** в Ollama туда **не влезет** (ей нужно ~6+ ГБ только на веса модели).

**Варианты:**

| Вариант | Описание |
|--------|----------|
| **A** | Поставить на сервер **лёгкую модель** (см. ниже) и Ollama — бот будет работать автономно. |
| **B** | **Ollama оставить у себя на ПК**, на сервер перенести только бота; бот будет ходить в твой Ollama по интернету (нужен белый IP или туннель: ngrok / Cloudflare Tunnel). |
| **C** | Использовать **облачный LLM API** (OpenAI, Groq, и т.д.) — в коде заменить вызов Ollama на вызов API. |

Ниже инструкция для **варианта A**: сервер + Ollama + лёгкая модель.

---

## 1. Папка и пользователь

Бот ставим отдельно от админки и БД, например в домашнюю папку пользователя:

```bash
sudo -u YOUR_USER bash -c 'cd ~ && mkdir -p tgbot && cd tgbot && pwd'
```

Подставь своего пользователя (например `root` или отдельного `tgbot`). Дальше везде `YOUR_USER` и `/home/YOUR_USER/tgbot` замени на свои.

---

## 2. Копирование файлов проекта на сервер

С **локального ПК** (из папки TgBot) залей файлы на сервер. Варианты:

**Через SCP (с ПК):**
```bash
scp -r bot.py requirements.txt .env.example deploy/tgbot.service YOUR_USER@IP_СЕРВЕРА:~/tgbot/
# папку deploy положить в tgbot, потом на сервере переместить .service куда нужно
```

**Или через архив:**
- Упакуй в ZIP: `bot.py`, `requirements.txt`, `.env.example`, папку `deploy`, папку `chat_logs` (пустую или с логами).
- Залей архив на сервер (SFTP, SCP, панель хостинга).
- На сервере: `cd ~/tgbot && unzip tgbot.zip`.

На сервере в `~/tgbot` должны быть минимум: `bot.py`, `requirements.txt`, `.env.example`, и папка `deploy` с `tgbot.service`.

---

## 3. Python и зависимости

На сервере:

```bash
cd ~/tgbot
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

(Лаунчер с окном на сервере не нужен — можно в `requirements.txt` на сервере удалить строки `customtkinter` и `psutil`, чтобы не ставить лишнее, или оставить — бот и так запускается.)

---

## 4. Ollama и лёгкая модель (вариант A)

Установка Ollama под Linux:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Модель **не больше 2–3 ГБ** в квантизации, иначе сервер с 2 ГБ упрётся в память. Примеры:

```bash
ollama pull qwen2:0.5b
# или
ollama pull phi2
# или
ollama pull tinyllama
```

Проверка:

```bash
ollama list
ollama run qwen2:0.5b "Привет"
```

В `.env` бота укажи выбранную модель (см. ниже).

---

## 5. Настройка бота (.env)

На сервере:

```bash
cd ~/tgbot
cp .env.example .env
nano .env
```

Заполни (подставь свой токен и модель):

```env
BOT_TOKEN=your_bot_token_from_botfather
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2:0.5b
```

Сохрани (Ctrl+O, Enter, Ctrl+X). Файл `.env` не коммить и никому не отдавать.

---

## 6. Запуск как сервис (systemd)

Скопировать unit-файл и подставить пользователя и путь:

```bash
sudo cp ~/tgbot/deploy/tgbot.service /etc/systemd/system/
sudo nano /etc/systemd/system/tgbot.service
```

В файле замени:
- `YOUR_USER` — твой пользователь (например `root` или `tgbot`);
- `/home/YOUR_USER/tgbot` — полный путь к папке бота (например `/root/tgbot` или `/home/tgbot/tgbot`).

Пример готового блока:

```ini
[Service]
User=root
WorkingDirectory=/root/tgbot
EnvironmentFile=/root/tgbot/.env
ExecStart=/root/tgbot/venv/bin/python bot.py
Restart=always
RestartSec=10
```

Дальше:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tgbot
sudo systemctl start tgbot
sudo systemctl status tgbot
```

Логи:

```bash
journalctl -u tgbot -f
```

Остановка/перезапуск:

```bash
sudo systemctl stop tgbot
sudo systemctl restart tgbot
```

---

## 7. Проверка

- В Telegram напиши боту — должен отвечать.
- Если ошибка про Ollama: `curl http://localhost:11434/api/tags` — должен вернуть JSON с моделями.
- Если бот падает: смотри `journalctl -u tgbot -n 50`.

---

## 8. Вариант B: Ollama на твоём ПК, бот на сервере

Если хочешь оставить Gemma 2 9B на домашнем ПК:

1. На ПК Ollama слушает только localhost. Нужно выставить в интернет через туннель, например **ngrok**:  
   `ngrok http 11434`  
   Получишь URL вида `https://xxxx.ngrok.io`.

2. На сервере в `.env` бота:
   ```env
   OLLAMA_URL=https://xxxx.ngrok.io
   OLLAMA_MODEL=gemma2:9b
   ```
   (В коде бота к URL автоматически дописывается `/v1`.)

3. Перезапуск бота: `sudo systemctl restart tgbot`.

Минус: пока туннель не поднят на ПК, бот на сервере не сможет достучаться до модели.

---

## Кратко

- Бот и админка/БД раздельно: отдельная папка, отдельный сервис.
- На 2 ГБ RAM используй лёгкую модель (qwen2:0.5b, phi2, tinyllama) или внешний Ollama/API.
- Токен и настройки — только в `.env`, не в коде.
- Управление: `systemctl start|stop|restart|status tgbot`, логи — `journalctl -u tgbot -f`.
