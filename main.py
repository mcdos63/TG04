import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, select, desc
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import *

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- Состояние FSM для отправки сообщения ---
class SendMessageState(StatesGroup):
    waiting_for_text = State()
class RegisterPhone(StatesGroup):
    waiting_for_phone = State()

# Настройка базы данных
DATABASE_URL = "sqlite+aiosqlite:///users.db"
engine = create_async_engine(DATABASE_URL, echo=False)
Base = declarative_base()
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# --- Модели ---
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)

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

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

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

# --- Обработка нажатия кнопки "Отправить сообщение" ---
@dp.callback_query(F.data == "send")
async def ask_for_message(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пожалуйста, введите сообщение:")
    await state.set_state(SendMessageState.waiting_for_text)
    await callback.answer()

# --- Получение текста и сохранение в БД ---
@dp.message(SendMessageState.waiting_for_text)
async def save_user_text(message: Message, state: FSMContext):
    user = await get_user_by_id(message.from_user.id)
    if not user:
        await message.answer("Вы ещё не зарегистрированы.")
        await state.clear()
        return

    # Сохраняем сообщение
    async with AsyncSessionLocal() as session:
        new_info = Info(user_id=user.user_id, text=message.text)
        session.add(new_info)
        await session.commit()

    await message.answer("✅ Ваше сообщение сохранено!", reply_markup=inline_3)
    await state.clear()

@dp.callback_query(F.data == "registration")
async def registration(callback: CallbackQuery):
    await callback.message.answer("Пожалуйста, поделитесь номером телефона:", reply_markup=choose_phone_kb)
    await callback.answer()

@dp.message(F.contact)
async def save_phone(message: Message):
    phone = message.contact.phone_number
    name = message.from_user.full_name
    async with AsyncSessionLocal() as session:
        new_user = User(user_id=message.from_user.id, name=name, phone=phone)
        session.add(new_user)
        await session.commit()
    await message.answer(f"Спасибо, {name}! Ваш номер телефона: {phone}", reply_markup=ReplyKeyboardRemove())
    await message.answer("Выберите, что делать дальше:", reply_markup=inline_3)

@dp.message(F.text.endswith("Ввести номер вручную"))
async def ask_phone_manually(message: Message, state: FSMContext):
    await message.answer("Введите номер телефона в формате +7XXXXXXXXXX или 89XXXXXXXXX:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegisterPhone.waiting_for_phone)

@dp.message(RegisterPhone.waiting_for_phone)
async def process_phone_input(message: Message, state: FSMContext):
    phone = message.text.strip()
    phone = normalize_phone_number(phone)
    if not phone:
        await message.answer("❗ Неверный формат номера. Попробуйте снова.")
        return
    name = message.from_user.full_name
    async with AsyncSessionLocal() as session:
        new_user = User(user_id=message.from_user.id, name=name, phone=phone)
        session.add(new_user)
        await session.commit()

    await message.answer(f"Спасибо, {name}! Ваш номер телефона: {phone}")
    await message.answer("Выберите, что делать дальше:", reply_markup=inline_3)
    await state.clear()

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


@dp.message(Command("messages"))
async def show_user_messages(message: Message):
    user = await get_user_by_id(message.from_user.id)
    if not user:
        await message.answer("Вы ещё не зарегистрированы.")
        return

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Info).where(Info.user_id == user.user_id).order_by(desc(Info.date)).limit(10)
        )
        messages = result.scalars().all()

    if not messages:
        await message.answer("У вас пока нет сохранённых сообщений.")
        return

    response = "Ваши последние сообщения:\n\n"
    for msg in messages:
        response += f"🕒 {msg.date.strftime('%d.%m %H:%M')}\n💬 {msg.text}\n\n"

    await message.answer(response)

from aiogram.types import Message
from sqlalchemy import select, join
from sqlalchemy.orm import aliased

@dp.message(Command("all_messages"))
async def show_all_messages(message: Message):
    # # Проверка прав администратора (по user_id, например)
    # if message.from_user.id != ADMIN_ID:
    #     await message.answer("⛔ У вас нет доступа к этой команде.")
    #     return

    async with AsyncSessionLocal() as session:
        # Объединяем таблицы User и Info по user_id
        j = join(User, Info, User.user_id == Info.user_id)
        result = await session.execute(
            select(User.user_id, User.name, Info.text, Info.date).select_from(j).order_by(Info.date.desc())
        )
        records = result.all()

    if not records:
        await message.answer("🗃 Сообщения не найдены.")
        return

    # Формируем текст ответа
    response = "📑 Все сохранённые сообщения:\n\n"
    for user_id, name, text, date in records:
        response += (
            f"👤 {name} (ID: {user_id})\n"
            f"🕒 {date.strftime('%d.%m %H:%M')}\n"
            f"💬 {text}\n\n"
        )

    # Ограничим длину Telegram-сообщения
    if len(response) > 4000:
        await message.answer("⚠️ Сообщений слишком много. Вывожу только первые.")
        await message.answer(response[:4000])
    else:
        await message.answer(response)


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
