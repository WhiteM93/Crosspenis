"""HTTP relay: Biota POST → Telegram (aiogram Bot)."""

import os

from aiohttp import web
from aiogram import Bot

BIOTA_SECRET = os.getenv("BIOTA_RELAY_SECRET", "")
DEFAULT_CHAT_ID = os.getenv("BIOTA_DEFAULT_CHAT_ID", "")


async def biota_notify(request: web.Request) -> web.Response:
    if BIOTA_SECRET:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {BIOTA_SECRET}":
            return web.json_response({"ok": False, "error": "unauthorized"}, status=401)

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "invalid json"}, status=400)

    text = (data.get("text") or "").strip()
    if not text:
        return web.json_response({"ok": False, "error": "empty text"}, status=400)

    bot: Bot = request.app["bot"]
    chats = data.get("chat_ids") or []
    if not chats and DEFAULT_CHAT_ID:
        chats = [DEFAULT_CHAT_ID]
    if not chats:
        return web.json_response({"ok": False, "error": "no chat_ids"}, status=400)

    for cid in chats:
        await bot.send_message(chat_id=str(cid), text=text)

    return web.json_response({"ok": True})


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
