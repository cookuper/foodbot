
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import sqlite3
import asyncio
import requests

API_TOKEN = '8066927688:AAFipaqyM4qoUODZ705PDocSZSSEEGWCVik'
PUPPETEER_URL = 'https://foodbot-t75k.onrender.com/generate?query='

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
c.execute("""
    CREATE TABLE IF NOT EXISTS manual_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT
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

class ManualInput(StatesGroup):
    request = State()

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

@dp.callback_query_handler(lambda c: c.data == 'manual')
async def manual_entry(callback_query: types.CallbackQuery):
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text="✍ Введите список продуктов и бюджет (например: пятерочка лапша сосиски майонез 700р):"
    )
    await ManualInput.request.set()

@dp.message_handler(state=ManualInput.request)
async def process_manual_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    c.execute("INSERT INTO manual_requests (user_id, message) VALUES (?, ?)", (user_id, text))
    conn.commit()

    try:
        response = requests.get(PUPPETEER_URL + text)
        if response.status_code == 200:
            result = response.text
        else:
            result = "⚠ Ошибка от сервера Puppeteer."
    except Exception as e:
        result = f"❌ Не удалось связаться с сервером: {e}"

    await message.answer(f"🔍 Запрос принят: \n{text}\n\n📦 Ответ: \n{result}", reply_markup=main_menu)
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'random')
async def dummy_handler(callback_query: types.CallbackQuery):
    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"🎲 Рандомная функция пока в разработке. Возвращаюсь в меню..."
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
