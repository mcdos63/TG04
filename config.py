from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

BOT_TOKEN = '7810024725:AAGqkFAfZ6rX15YGYW_miu4Km0d7lg02n0Q'


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

request_phone_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]], resize_keyboard=True,  one_time_keyboard=True)


