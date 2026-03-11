"""
Telegram-бот с прямой связью с локальной моделью (Ollama).
Настройки: .env или переменные окружения (BOT_TOKEN, OLLAMA_URL, OLLAMA_MODEL).
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from openai import OpenAI
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# ----- Настройки (только из переменных окружения, без секретов в коде) -----
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    print("Задай BOT_TOKEN в .env или переменных окружения (см. .env.example)")
    sys.exit(1)

OLLAMA_URL = (os.environ.get("OLLAMA_URL") or "http://localhost:11434").rstrip("/")
if not OLLAMA_URL.endswith("/v1"):
    OLLAMA_URL = OLLAMA_URL + "/v1"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2:9b")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "120"))
# Контекст: последние N пар сообщений (user + assistant)
CONTEXT_LEN = 4
# Файл для сохранения переписки теста /test10
TEST_CHAT_LOG = Path(__file__).parent / "local" / "test_chat_log.txt"
# Папка логов общения: для каждого user_id свой файл local/chat_logs/{user_id}.txt
CHAT_LOGS_DIR = Path(__file__).parent / "local" / "chat_logs"
# 10 тестовых реплик для прогона через модель (как в боте)
TEST_PHRASES = [
    "Привет, как дела?",
    "Что посоветуешь по ноутбуку — тормозит?",
    "Ты кто вообще?",
    "Сколько стоит починить экран?",
    "Норм, спасибо. А вирусы чистить умеешь?",
    "Погода сегодня ничего?",
    "Ок, тогда до связи",
    "Какой у тебя любимый гаджет?",
    "Срочно нужна помощь с компом",
    "Пока!",
]
# --------------------

def _server_date() -> str:
    d = datetime.now()
    days = ("пн", "вт", "ср", "чт", "пт", "сб", "вс")
    return f"{d:%d.%m.%Y}, {days[d.weekday()]}, {d:%H:%M}"


def _is_date_question(text: str) -> bool:
    t = text.lower().strip()
    return any(w in t for w in ("какой сегодня", "какой день", "какая дата", "какой год", "какое время", "сейчас год", "какое число", "какой сейчас"))


bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

client = OpenAI(base_url=OLLAMA_URL, api_key="ollama", timeout=OLLAMA_TIMEOUT)
# История по user_id: список {"role": "user"|"assistant", "content": "..."}
_history: dict[int, list[dict[str, str]]] = {}


def _append_chat_log(user_id: int, username: str, direction: str, text: str) -> None:
    """Дописать строку в лог общения пользователя. Файл: chat_logs/{user_id}.txt"""
    if user_id <= 0:
        return
    try:
        CHAT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_file = CHAT_LOGS_DIR / f"{user_id}.txt"
        safe = (text or "").replace("\n", " ").replace("\r", "")[:2000]
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts} | {direction} | {safe}\n"
        if not log_file.exists():
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"# Лог чата | user_id={user_id} | @{username or '?'}\n")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def _chat(user_id: int, text: str) -> str:
    """Отправить сообщение в модель, вернуть ответ. Синхронный вызов."""
    history = _history.get(user_id, [])[-CONTEXT_LEN * 2 :]
    today = _server_date()
    system = (
        f"Ты Паша Техник. Сейчас: {today}. Злой, грубый, материшься и оскорбляешь по-русски. Не вежливый, не успокаиваешь.\n"
        "Мат — разнообразный, не одно и то же слово подряд. Используй по-разному: блять, бля, нахуй, похуй, хуйня, херня, пиздец, сука, жопа, заебись, заебал, охуеть, выёбываться, мудак, мудила, долбоёб, придурок, дебил, пидор, уёбок, отстой, говно, залупа, отвали, пошёл нахуй, хуй тебе, нихуя, дохуя, нахуя, пиздато, заебало, в пизду — чередуй, не спамь одно слово.\n"
        "Ответы короткие или средние, по существу: дай мысль/совет/шутку, не воду. На дату/год — из «Сейчас». На /start — грубо (чё надо, ну что), не «Понял. Давай». Кто ты — только если спросили. Без списков, без эмодзи. Один пробел между словами. Не пиши «пи» — пиши «жопу» или «нахуй»."
    )
    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": text})

    kwargs = dict(model=OLLAMA_MODEL, messages=messages, max_tokens=300, temperature=0.7)
    if "11434" in OLLAMA_URL:
        kwargs["extra_body"] = {"options": {"think": False}}

    r = client.chat.completions.create(**kwargs)
    reply = (r.choices[0].message.content or "").strip()
    reply = " ".join(reply.split())  # убрать двойные пробелы и переносы
    if " в пи " in reply or reply.endswith(" в пи"):
        reply = reply.replace(" в пи ", " нахуй ").replace(" в пи", " нахуй")
    reply = reply or "Пустой ответ."
    # Если спрашивали дату/год, а в ответе нет цифр года — подставить актуальную дату
    if _is_date_question(text) and not any(c.isdigit() for c in reply):
        reply = f"Сейчас {today}."
    return reply


@router.message(Command("test10"))
async def cmd_test10(message: types.Message):
    """Прогнать 10 тестовых реплик через модель и сохранить переписку в файл."""
    await message.answer("Запускаю 10 тестов, жди…")
    test_uid = -1  # отдельный «пользователь» для теста, контекст свой
    _history[test_uid] = []
    lines = [f"=== Тест 10 реплик | {datetime.now():%Y-%m-%d %H:%M:%S} ===\n"]
    for i, phrase in enumerate(TEST_PHRASES, 1):
        try:
            reply = await asyncio.to_thread(_chat, test_uid, phrase)
        except Exception as e:
            reply = f"[Ошибка: {e}]"
        _history.setdefault(test_uid, [])
        _history[test_uid] = (_history[test_uid] + [
            {"role": "user", "content": phrase},
            {"role": "assistant", "content": reply},
        ])[-CONTEXT_LEN * 2 :]
        lines.append(f"[{i}] User: {phrase}\n")
        lines.append(f"    Bot:  {reply}\n")
    try:
        TEST_CHAT_LOG.write_text("".join(lines), encoding="utf-8")
        await message.answer(f"Готово. Переписка сохранена в <code>{TEST_CHAT_LOG.name}</code>")
    except Exception as e:
        await message.answer(f"Тесты прошли, но сохранить не удалось: {e}")


@router.message(F.text)
async def on_message(message: types.Message):
    text = (message.text or "").strip()
    if not text:
        return

    uid = message.from_user.id if message.from_user else 0
    username = (message.from_user.username or "") if message.from_user else ""
    _append_chat_log(uid, username, "IN", text)
    await bot.send_chat_action(message.chat.id, "typing")

    try:
        reply = await asyncio.to_thread(_chat, uid, text)
    except Exception as e:
        reply = f"Ошибка: {e}. Проверь, что Ollama запущен и модель {OLLAMA_MODEL} есть (ollama list)."

    _append_chat_log(uid, username, "OUT", reply)
    # Сохранить в контекст
    _history.setdefault(uid, [])
    _history[uid] = (_history[uid] + [
        {"role": "user", "content": text},
        {"role": "assistant", "content": reply},
    ])[-CONTEXT_LEN * 2 :]

    if len(reply) > 4096:
        reply = reply[:4090] + "..."
    await message.answer(reply)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
