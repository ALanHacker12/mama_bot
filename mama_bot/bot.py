import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ========== ТВОЙ ТОКЕН ==========
TOKEN = "8740387123:AAHET8K33FpV0XRAAu2rIubP3zM4qTA01Yk"

# ========== НАСТРОЙКИ ==========
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ========== БАЗА ДАННЫХ (в памяти) ==========
user_data = {}

# ========== ГЛАВНОЕ МЕНЮ ==========
def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 План на сегодня", callback_data="plan")],
        [InlineKeyboardButton(text="💰 Добавить продажу", callback_data="sale")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📝 Мои вещи", callback_data="items")]
    ])
    return kb

# ========== СОСТОЯНИЯ ДЛЯ ПРОДАЖ ==========
class SaleForm(StatesGroup):
    name = State()
    price = State()

# ========== СОСТОЯНИЯ ДЛЯ ДОБАВЛЕНИЯ ВЕЩЕЙ ==========
class ItemForm(StatesGroup):
    name = State()
    size = State()
    color = State()
    price = State()

# ========== КОМАНДА /start ==========
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    user_id = str(message.from_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {
            "items": [],
            "sales": [],
            "money": {
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

# ========== КНОПКА "ПЛАН" ==========
@dp.callback_query(lambda c: c.data == "plan")
async def show_plan(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    plan_text = (
        "📅 <b>План на сегодня</b>\n\n"
        "1️⃣ Сфотографируй 5 новых вещей\n"
        "2️⃣ Выложи их на Авито в 19:00\n"
        "3️⃣ Обнови 10 старых объявлений\n"
        "4️⃣ Ответь на все сообщения\n"
        "5️⃣ Запиши продажи в бота\n\n"
        "🎯 Цель на сегодня: 3 продажи"
    )
    await callback.message.edit_text(plan_text, parse_mode="HTML")
    await callback.answer()

# ========== КНОПКА "СТАТИСТИКА" ==========
@dp.callback_query(lambda c: c.data == "stats")
async def show_stats(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    data = user_data.get(user_id, {})
    sales = data.get("sales", [])
    money = data.get("money", {})
    
    total_sales = len(sales)
    total_revenue = sum(s.get("price", 0) for s in sales)
    
    stats_text = (
        f"📊 <b>Твоя статистика</b>\n\n"
        f"📦 Продано: {total_sales} вещей\n"
        f"💰 Выручка: {total_revenue} ₽\n\n"
        f"<b>💰 Конверты:</b>\n"
        f"👩 Себе: {money.get('salary', 0)} ₽\n"
        f"📦 Оборот: {money.get('turnover', 0)} ₽\n"
        f"📮 Почта: {money.get('post', 0)} ₽\n"
        f"🛡️ Подушка: {money.get('pillow', 0)} ₽\n"
        f"✨ Мечта: {money.get('dream', 0)} ₽"
    )
    await callback.message.edit_text(stats_text, parse_mode="HTML")
    await callback.answer()

# ========== КНОПКА "МОИ ВЕЩИ" ==========
@dp.callback_query(lambda c: c.data == "items")
async def show_items(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    items = user_data.get(user_id, {}).get("items", [])
    
    if not items:
        text = "📝 У тебя пока нет вещей в списке.\n\n"
        text += "Добавь первую вещь командой:\n"
        text += "<code>/add_item</code>"
    else:
        text = "📝 <b>Твои вещи:</b>\n\n"
        for i, item in enumerate(items[-10:], 1):
            text += f"{i}. {item['name']} | {item['size']} | {item['color']} | {item['price']} ₽\n"
        if len(items) > 10:
            text += f"\n...и ещё {len(items)-10} вещей"
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

# ========== КНОПКА "ДОБАВИТЬ ПРОДАЖУ" ==========
@dp.callback_query(lambda c: c.data == "sale")
async def start_sale(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("💰 Напиши название вещи, которую продала:")
    await state.set_state(SaleForm.name)
    await callback.answer()

@dp.message(SaleForm.name)
async def get_sale_price(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("💰 Напиши цену продажи (число):")
    await state.set_state(SaleForm.price)

@dp.message(SaleForm.price)
async def save_sale(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        data = await state.get_data()
        name = data.get("name")
        
        user_id = str(message.from_user.id)
        
        user_data[user_id]["sales"].append({
            "name": name,
            "price": price,
            "date": datetime.now().strftime("%d.%m.%Y")
        })
        
        money = user_data[user_id]["money"]
        money["salary"] += int(price * 0.3)
        money["turnover"] += int(price * 0.4)
        money["post"] += int(price * 0.15)
        money["pillow"] += int(price * 0.1)
        money["dream"] += int(price * 0.05)
        
        await message.answer(
            f"✅ Продажа записана!\n\n"
            f"📦 {name} — {price} ₽\n\n"
            f"<b>Деньги разложены:</b>\n"
            f"👩 Себе (30%): {int(price*0.3)} ₽\n"
            f"📦 Оборот (40%): {int(price*0.4)} ₽\n"
            f"📮 Почта (15%): {int(price*0.15)} ₽\n"
            f"🛡️ Подушка (10%): {int(price*0.1)} ₽\n"
            f"✨ Мечта (5%): {int(price*0.05)} ₽\n\n"
            "Так держать! 💪",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Ошибка! Введи число, например: 1200")

# ========== КОМАНДА /add_item ==========
@dp.message(Command("add_item"))
async def start_add_item(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("📝 Напиши название вещи:")
    await state.set_state(ItemForm.name)

@dp.message(ItemForm.name)
async def get_item_size(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📏 Напиши размер (46, M, L):")
    await state.set_state(ItemForm.size)

@dp.message(ItemForm.size)
async def get_item_color(message: Message, state: FSMContext):
    await state.update_data(size=message.text)
    await message.answer("🎨 Напиши цвет:")
    await state.set_state(ItemForm.color)

@dp.message(ItemForm.color)
async def get_item_price(message: Message, state: FSMContext):
    await state.update_data(color=message.text)
    await message.answer("💰 Напиши цену (число):")
    await state.set_state(ItemForm.price)

@dp.message(ItemForm.price)
async def save_item(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        data = await state.get_data()
        
        user_id = str(message.from_user.id)
        user_data[user_id]["items"].append({
            "name": data.get("name"),
            "size": data.get("size"),
            "color": data.get("color"),
            "price": price
        })
        
        await message.answer(
            f"✅ Вещь добавлена!\n\n"
            f"📦 {data.get('name')}\n"
            f"📏 Размер: {data.get('size')}\n"
            f"🎨 Цвет: {data.get('color')}\n"
            f"💰 Цена: {price} ₽",
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Ошибка! Введи число")

# ========== ЗАПУСК БОТА ==========
async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
