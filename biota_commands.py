"""Команды /svodka — запрос сводки у Biota API."""

import os

import aiohttp
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards import BTN_DAY, BTN_HELP, BTN_NIGHT, BTN_SVODKA, HELP_TEXT, main_keyboard

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


async def _reply_summary(message: Message, slot: str) -> None:
    wait = await message.answer("⏳ Запрашиваю сводку…", reply_markup=main_keyboard())
    ok, text = await _request_summary(message.chat.id, slot)
    await wait.edit_text(text if ok else f"❌ {text}")


@router.message(Command("svodka"))
@router.message(F.text == BTN_SVODKA)
async def cmd_svodka(message: Message):
    await _reply_summary(message, "auto")


@router.message(Command("svodka_d"))
@router.message(F.text == BTN_DAY)
async def cmd_svodka_day(message: Message):
    await _reply_summary(message, "morning")


@router.message(Command("svodka_n"))
@router.message(F.text == BTN_NIGHT)
async def cmd_svodka_night(message: Message):
    await _reply_summary(message, "evening")


@router.message(Command("help"))
@router.message(F.text == BTN_HELP)
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, reply_markup=main_keyboard())
