"""Crosspenis — точка входа."""

import os
import sys
import asyncio
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

from biota_relay import start_biota_relay
from biota_commands import router as biota_router
from keyboards import BOT_COMMANDS, HELP_TEXT, START_TEXT, main_keyboard

TOKEN = (os.environ.get("TOKEN") or os.environ.get("BOT_TOKEN") or "").strip()
if not TOKEN:
    print("Задай TOKEN в .env (см. .env.example)")
    sys.exit(1)

client = Bot(token=TOKEN, default=DefaultBotProperties())
dp = Dispatcher()
router = Router()
dp.include_router(biota_router)
dp.include_router(router)


@router.message(Command("start"))
async def on_start(message: types.Message):
    await message.answer(START_TEXT, reply_markup=main_keyboard())


@router.message(F.text == "!help")
async def on_help(message: types.Message):
    await message.answer(HELP_TEXT, reply_markup=main_keyboard())


async def main():
    await client.set_my_commands(BOT_COMMANDS)
    await start_biota_relay(client)
    await dp.start_polling(client)


if __name__ == "__main__":
    asyncio.run(main())
