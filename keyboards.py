"""Клавиатуры и подписи кнопок."""

from aiogram.types import BotCommand, KeyboardButton, ReplyKeyboardMarkup

BTN_SVODKA = "📊 Сводка"
BTN_DAY = "☀️ Дневная"
BTN_NIGHT = "🌙 Ночная"
BTN_HELP = "❓ Справка"

START_TEXT = (
    "Бот Biota — сводки по СКУД.\n\n"
    "Нажмите кнопку внизу или используйте команды в меню «/»."
)

HELP_TEXT = (
    "Кнопки внизу экрана:\n"
    f"• {BTN_SVODKA} — авто (до 15:00 дневная, после — ночная)\n"
    f"• {BTN_DAY} — только дневная смена\n"
    f"• {BTN_NIGHT} — только ночная смена\n\n"
    "Команды: /svodka, /svodka_d, /svodka_n"
)

BOT_COMMANDS = [
    BotCommand(command="svodka", description="Сводка (авто)"),
    BotCommand(command="svodka_d", description="Дневная смена"),
    BotCommand(command="svodka_n", description="Ночная смена"),
    BotCommand(command="help", description="Справка"),
]


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_SVODKA)],
            [KeyboardButton(text=BTN_DAY), KeyboardButton(text=BTN_NIGHT)],
            [KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие…",
    )
