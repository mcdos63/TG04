import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import *

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Настройка базы данных
DATABASE_URL = "sqlite+aiosqlite:///users.db"
engine = create_async_engine(DATABASE_URL, echo=False)
Base = declarative_base()
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# --- Модели ---
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)

    def __repr__(self):
        return f"<User {self.user_id}: {self.name}>"


class Info(Base):
    __tablename__ = 'info'
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)

    def __repr__(self):
        return f"<Info {self.user_id}: {self.text}>"


# --- Создание таблиц ---
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_user_by_id(user_id: int) -> User | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        return user

# --- Хендлеры ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Я бот-регистратор!", reply_markup=inline_1)


@dp.callback_query(F.data == "entry")
async def entry(callback: CallbackQuery):
    await callback.answer("Информация загружается...")
    user = await get_user_by_id(callback.from_user.id)
    if user:
        await callback.message.edit_text(f"Привет! Вы уже зарегистрированы как {user.name}", reply_markup=inline_3)
        await callback.answer()
    else:
        await callback.message.edit_text(f'Привет, {callback.from_user.full_name}. Зарегистрируемся?', reply_markup=inline_2)
        await callback.answer()

@dp.callback_query(F.data == "delete")
async def delete_user(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(callback.from_user.id)
        if user:
            await session.delete(user)
            await session.commit()
            await callback.message.edit_text("Ваш аккаунт удален. Для регистрации нажмите /start")
        else:
            await callback.message.edit_text("Вы не зарегистрированы.")
    await callback.answer()

@dp.callback_query(F.data == "exit")
async def exit(callback: CallbackQuery):
    await callback.message.edit_text(f"До свидания , {callback.from_user.full_name}!")
    await callback.answer()

@dp.message(Command("users"))
async def get_all_users(message: Message):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

    if not users:
        await message.answer("Пользователей не найдено.")
    else:
        text = "👥 Список пользователей:\n\n"
        for u in users:
            text += f"🆔 {u.user_id}\n👤 {u.name}\n📞 {u.phone or 'Нет телефона'}\n\n"
        await message.answer(text)

@dp.message(Command("info"))
async def show_info(message: Message):
    user = await get_user_by_id(message.from_user.id)
    if user:
        await message.answer(f"🧾 Ваша информация:\nИмя: {user.name}\nТелефон: {user.phone}")
    else:
        await message.answer("Вы еще не зарегистрированы.")

@dp.message(Command("links"))
async def links(message: Message):
    await message.answer("Медиа:", reply_markup=inline_4)


# --- Точка входа ---
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("Бот включен!")
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот выключен пользователем!")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
