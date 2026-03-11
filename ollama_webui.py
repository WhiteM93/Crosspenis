"""
Минимальный веб-интерфейс для Ollama: выбор модели, температура, чат.
Запуск: python ollama_webui.py
Открыть в браузере: http://localhost:8765
"""
import json
import httpx
from pathlib import Path

try:
    from fastapi import FastAPI, Body
    from fastapi.responses import HTMLResponse
    import uvicorn
except ImportError:
    print("Нужно установить: pip install fastapi uvicorn httpx")
    raise

OLLAMA_URL = "http://localhost:11434"
PORT = 8765

app = FastAPI(title="Ollama Web UI")
client = httpx.Client(base_url=OLLAMA_URL, timeout=120.0)

HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Ollama — настройка модели</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; max-width: 720px; margin: 0 auto; padding: 1rem; background: #1a1a1a; color: #e0e0e0; }
    h1 { font-size: 1.25rem; }
    .row { margin-bottom: 1rem; }
    label { display: block; margin-bottom: 0.25rem; color: #aaa; }
    select, input[type="number"], input[type="text"], button { padding: 0.5rem; border-radius: 6px; border: 1px solid #444; background: #2a2a2a; color: #e0e0e0; }
    input[type="text"] { width: 100%; }
    button { cursor: pointer; margin-right: 0.5rem; }
    button.primary { background: #0d6efd; border-color: #0d6efd; }
    #chat { height: 320px; overflow-y: auto; border: 1px solid #444; border-radius: 6px; padding: 0.75rem; background: #252525; margin-bottom: 0.5rem; }
    .msg { margin-bottom: 0.5rem; }
    .msg.user { color: #7df; }
    .msg.assistant { color: #afa; white-space: pre-wrap; }
    .error { color: #f88; }
  </style>
</head>
<body>
  <h1>Ollama — чат и настройки модели</h1>
  <div class="row">
    <label>Модель</label>
    <select id="model"><option>Загрузка...</option></select>
  </div>
  <div class="row">
    <label>Temperature (0–2, по умолчанию 0.7)</label>
    <input type="number" id="temperature" min="0" max="2" step="0.1" value="0.7" style="width: 6rem;">
  </div>
  <div class="row">
    <label>Контекст (num_ctx, токенов)</label>
    <input type="number" id="num_ctx" min="512" max="32768" step="512" value="2048" style="width: 8rem;">
  </div>
  <div id="chat"></div>
  <div class="row">
    <input type="text" id="input" placeholder="Сообщение..." autocomplete="off">
    <button class="primary" id="send">Отправить</button>
  </div>
  <script>
    const chat = document.getElementById('chat');
    const modelSelect = document.getElementById('model');
    const temperature = document.getElementById('temperature');
    const numCtx = document.getElementById('num_ctx');
    const input = document.getElementById('input');
    const sendBtn = document.getElementById('send');

    let messages = [];

    async function loadModels() {
      const r = await fetch('/api/models');
      const data = await r.json();
      modelSelect.innerHTML = data.models.map(m => '<option value="' + m.name + '">' + m.name + '</option>').join('') || '<option>Нет моделей</option>';
    }

    function addMsg(role, text) {
      const div = document.createElement('div');
      div.className = 'msg ' + role;
      div.textContent = text;
      chat.appendChild(div);
      chat.scrollTop = chat.scrollHeight;
    }

    sendBtn.addEventListener('click', async () => {
      const text = input.value.trim();
      if (!text) return;
      addMsg('user', text);
      messages.push({ role: 'user', content: text });
      input.value = '';
      sendBtn.disabled = true;
      try {
        const r = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model: modelSelect.value,
            messages: messages,
            temperature: parseFloat(temperature.value),
            num_ctx: parseInt(num_ctx.value, 10)
          })
        });
        const data = await r.json();
        if (data.error) {
          addMsg('assistant', 'Ошибка: ' + data.error);
        } else {
          const content = data.message && data.message.content ? data.message.content : data.response || '';
          addMsg('assistant', content);
          messages.push({ role: 'assistant', content: content });
        }
      } catch (e) {
        addMsg('assistant', 'Ошибка: ' + e.message);
      }
      sendBtn.disabled = false;
    });
    input.addEventListener('keydown', e => { if (e.key === 'Enter') sendBtn.click(); });

    loadModels();
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML


@app.get("/api/models")
def list_models():
    try:
        r = client.get("/api/tags")
        r.raise_for_status()
        data = r.json()
        return {"models": [{"name": m["name"]} for m in data.get("models", [])]}
    except Exception as e:
        return {"models": [], "error": str(e)}


from fastapi import Body


@app.post("/api/chat")
def chat_post(
    model: str = Body(..., embed=True),
    messages: list = Body(..., embed=True),
    temperature: float = Body(0.7, embed=True),
    num_ctx: int = Body(2048, embed=True),
):
    try:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_ctx": num_ctx},
        }
        r = client.post("/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        return {"message": data.get("message", {}), "response": data.get("message", {}).get("content", "")}
    except Exception as e:
        return {"error": str(e)}


def main():
    print(f"Ollama Web UI: http://localhost:{PORT}")
    print("Убедись, что Ollama запущена (localhost:11434).")
    uvicorn.run(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
