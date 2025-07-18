from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import re


def normalize_phone_number(phone: str) -> str | None:
    """
    Приводит номер телефона к формату +7XXXXXXXXXX.
    Возвращает нормализованный номер, либо None при ошибке.
    """
    phone = re.sub(r"[^\d+]", "", phone)  # Удаляем пробелы, скобки, тире, всё кроме цифр и плюса

    if phone.startswith("+"):
        digits = phone[1:]
        if digits.isdigit():
            return "+" + digits
    elif phone.startswith("8") and len(phone) == 11:
        return "+7" + phone[1:]
    elif phone.isdigit():
        return phone  # Просто цифры без "+"

    return None  # Не подходит под условия


BOT_TOKEN = 'ТОКЕН'

inline_1 = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Привет", callback_data='entry')],
    [InlineKeyboardButton(text="Пока", callback_data='exit')]
])

inline_2 = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Регистрация", callback_data='registration')],
    [InlineKeyboardButton(text="Пока", callback_data='exit')]
])

inline_3 = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отправить сообщение", callback_data='send')],
    [InlineKeyboardButton(text="Удалить из базы", callback_data='delete')],
    [InlineKeyboardButton(text="Пока", callback_data='exit')]
])

inline_4 = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Новости", url='https://russian.rt.com/')],
    [InlineKeyboardButton(text="Музыка", url='https://my.mail.ru/music/search/все%20хиты/')],
    [InlineKeyboardButton(text="Видео", url='https://www.tiktok.com/')]
])

# request_phone_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]], resize_keyboard=True,  one_time_keyboard=True)
choose_phone_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Поделиться контактом", request_contact=True)],
        [KeyboardButton(text="✍️ Ввести номер вручную")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
