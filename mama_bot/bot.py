import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# ========== ТВОЙ ТОКЕН ==========
TOKEN = "8740387123:AAHET8K33FpV0XRAAu2rIubP3zM4qTA01Yk"

# ========== НАСТРОЙКИ ==========
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ========== БАЗА ДАННЫХ (пока в памяти) ==========
user_data = {}

# ========== ГЛАВНОЕ МЕНЮ (клавиатура) ==========
def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 План на сегодня", callback_data="plan")],
        [InlineKeyboardButton(text="💰 Добавить продажу", callback_data="sale")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📝 Мои вещи", callback_data="items")]
    ])
    return kb

# ========== КОМАНДА /start ==========
@dp.message(Command("start"))
async def start(message: Message):
    user_id = str(message.from_user.id)
    
    # Создаём пустую базу для нового пользователя
    if user_id not in user_data:
        user_data[user_id] = {
            "items": [],     # список вещей
            "sales": [],     # список продаж
            "money": {       # 5 конвертов
                "salary": 0,
                "turnover": 0,
                "post": 0,
                "pillow": 0,
                "dream": 0
            }
        }
    
    await message.answer(
        "👋 Привет, мама! Я твой бизнес-помощник.\n"
        "Я буду помогать тебе продавать вещи на Авито.\n\n"
        "Выбери действие:",
        reply_markup=main_menu()
    )

# ========== ЗАПУСК БОТА ==========
async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())