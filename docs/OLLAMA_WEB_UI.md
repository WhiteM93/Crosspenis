# Веб-интерфейс для Ollama (настройка модели)

Оллama сама по себе — только API и консоль (`ollama run`). Чтобы настраивать модели через браузер, ставят сторонний веб-интерфейс.

---

## Локальный минимальный UI (в проекте)

В проекте есть скрипт **ollama_webui.py** — лёгкий веб-интерфейс без тяжёлых зависимостей (только FastAPI + uvicorn + httpx).

**Запуск:**
```bash
python ollama_webui.py
```

Открой в браузере: **http://localhost:8765**

В интерфейсе: выбор модели из списка (подтягивается из Ollama), поле Temperature, контекст (num_ctx), чат для проверки ответов. Убедись, что Ollama запущена (`localhost:11434`).

---

## Вариант 2: Open WebUI (полнофункциональный)

Удобный чат, выбор и загрузка моделей, настройки.

### Через Docker (если установлен Docker Desktop)

```bash
docker run -d --name openwebui -p 3000:8080 -v open-webui:/app/backend/data ghcr.io/open-webui/open-webui:main
```

Открой в браузере: **http://localhost:3000**  
При первом заходе создаётся аккаунт админа.

### Без Docker (через Python)

1. Установка:
   ```bash
   pip install open-webui
   ```
2. Запуск (Ollama должна быть уже запущена):
   ```bash
   open-webui serve
   ```
   По умолчанию интерфейс на **http://localhost:8080**.

В интерфейсе: **Settings → Connections** — указать адрес Ollama (`http://localhost:11434`), затем в **Models** можно выбирать и подтягивать модели.

---

## Вариант 3: Только консоль Ollama (без веба)

Если нужны только параметры модели (temperature, context и т.д.):

1. Запуск чата с моделью:
   ```bash
   ollama run gemma2:9b
   ```
   (или полный путь к `ollama.exe`, если не в PATH.)

2. В чате Ollama команды:
   - `/set parameter temperature 0.7` — температура
   - `/set parameter num_ctx 4096` — размер контекста
   - `/set nothink` / `/set think` — для моделей с thinking (Qwen и т.п.)

Изменения действуют в текущей сессии. Чтобы задать параметры по умолчанию для своей модели, создают **Modelfile** и делают `ollama create` (см. документацию Ollama).

---

## Итог

| Цель                         | Что делать                          |
|-----------------------------|--------------------------------------|
| Быстрый чат и настройки в браузере | **python ollama_webui.py** → http://localhost:8765 |
| Полный UI, загрузка моделей | **Open WebUI** (Docker или `pip install open-webui` + `open-webui serve`) |
| Только подкрутить параметры  | Консоль: `ollama run <модель>` и `/set parameter ...` |

После настройки модели в Open WebUI или в консоли бот в Telegram продолжит ходить в тот же Ollama API (`localhost:11434`) — менять ничего не нужно.
