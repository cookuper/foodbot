from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import sqlite3
import asyncio

API_TOKEN = '8066927688:AAFipaqyM4qoUODZ705PDocSZSSEEGWCVik'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

conn = sqlite3.connect("users.db")
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        phone TEXT,
        address TEXT
    )
""")
conn.commit()

main_menu = InlineKeyboardMarkup(row_width=1)
main_menu.add(
    InlineKeyboardButton("🎲 Случайный заказ", callback_data="random"),
    InlineKeyboardButton("🍽 Настроить комбо", callback_data="settings"),
    InlineKeyboardButton("✍ Ввести вручную", callback_data="manual"),
)

class UserData(StatesGroup):
    name = State()
    phone = State()
    address = State()

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("Добро пожаловать. Здесь ты можешь быстро собрать себе еду.", reply_markup=main_menu)

@dp.callback_query_handler(lambda c: c.data == 'settings')
async def process_settings(callback_query: types.CallbackQuery):
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Введите ваше имя:"
    )
    await UserData.name.set()

@dp.message_handler(state=UserData.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваш номер телефона:")
    await UserData.next()

@dp.message_handler(state=UserData.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите адрес доставки:")
    await UserData.next()

@dp.message_handler(state=UserData.address)
async def process_address(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = message.from_user.id

    c.execute("REPLACE INTO users (user_id, name, phone, address) VALUES (?, ?, ?, ?)",
              (user_id, user_data['name'], user_data['phone'], message.text))
    conn.commit()

    await message.answer("✅ Данные сохранены. Что будем делать дальше?", reply_markup=main_menu)
    await state.finish()

@dp.callback_query_handler(lambda c: c.data in ['random', 'manual'])
async def dummy_handler(callback_query: types.CallbackQuery):
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"Функция '{callback_query.data}' в разработке. Возвращаюсь в меню..."
    )
    await asyncio.sleep(2)
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="Выберите действие:",
        reply_markup=main_menu
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
