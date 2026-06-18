"""Команды /svodka — запрос сводки у Biota API."""

import os

import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

BIOTA_API_URL = os.getenv("BIOTA_API_URL", "")
BIOTA_SECRET = (
    os.getenv("BIOTA_RELAY_SECRET")
    or os.getenv("BIOTA_NOTIFY_RELAY_SECRET")
    or ""
)


async def _request_summary(chat_id: int, slot: str = "auto") -> tuple[bool, str]:
    if not BIOTA_API_URL or not BIOTA_SECRET:
        return False, "Biota API не настроен на боте"

    headers = {
        "Authorization": f"Bearer {BIOTA_SECRET}",
        "Content-Type": "application/json",
    }
    payload = {"chat_id": str(chat_id), "slot": slot}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                BIOTA_API_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                data = await resp.json()
    except Exception as exc:
        return False, f"Ошибка связи с Biota: {exc}"

    if not data.get("ok"):
        return False, data.get("error") or "ошибка Biota"

    if data.get("delivered"):
        return True, "Сводка отправлена в этот чат."

    return True, data.get("text") or "готово"


@router.message(Command("svodka"))
async def cmd_svodka(message: Message):
    ok, text = await _request_summary(message.chat.id, "auto")
    await message.answer(text if ok else f"❌ {text}")


@router.message(Command("svodka_d"))
async def cmd_svodka_day(message: Message):
    ok, text = await _request_summary(message.chat.id, "morning")
    await message.answer(text if ok else f"❌ {text}")


@router.message(Command("svodka_n"))
async def cmd_svodka_night(message: Message):
    ok, text = await _request_summary(message.chat.id, "evening")
    await message.answer(text if ok else f"❌ {text}")
