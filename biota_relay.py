"""HTTP relay: Biota POST → Telegram (aiogram Bot).

Принимает любой kind (attendance_summary, inventory, test и т.д.) —
достаточно непустого поля text.
"""

import os

from aiohttp import web
from aiogram import Bot

BIOTA_SECRET = (
    os.getenv("BIOTA_RELAY_SECRET")
    or os.getenv("BIOTA_NOTIFY_RELAY_SECRET")
    or ""
)


def _default_chat_ids() -> list[str]:
    raw = os.getenv("BIOTA_DEFAULT_CHAT_ID") or os.getenv("BIOTA_TELEGRAM_CHAT_IDS", "")
    return [part.strip() for part in raw.split(",") if part.strip()]


def _normalize_chat_ids(data: dict) -> list[str]:
    chats = data.get("chat_ids")
    if chats is None and data.get("chat_id") is not None:
        chats = [data["chat_id"]]
    if chats is None:
        return _default_chat_ids()
    if isinstance(chats, (str, int)):
        chats = [chats]
    return [str(cid).strip() for cid in chats if str(cid).strip()]


async def biota_notify(request: web.Request) -> web.Response:
    if BIOTA_SECRET:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {BIOTA_SECRET}":
            return web.json_response({"ok": False, "error": "unauthorized"}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "invalid json"}, status=400)

    kind = data.get("kind") or "unknown"
    text = (data.get("text") or "").strip()
    if not text:
        return web.json_response({"ok": False, "error": "empty text"}, status=400)

    chats = _normalize_chat_ids(data)
    if not chats:
        return web.json_response({"ok": False, "error": "no chat_ids"}, status=400)

    bot: Bot = request.app["bot"]
    for cid in chats:
        await bot.send_message(chat_id=cid, text=text)

    print(f"Biota relay: kind={kind} → {len(chats)} chat(s)")
    return web.json_response({"ok": True, "kind": kind, "delivered": len(chats)})


async def start_biota_relay(bot: Bot) -> web.AppRunner:
    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/api/biota/notify", biota_notify)

    port = int(os.getenv("BIOTA_RELAY_PORT", "8765"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()
    print(f"Biota relay: http://0.0.0.0:{port}/api/biota/notify")
    return runner
