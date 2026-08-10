import asyncio
import logging
import random
import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ========== ТОКЕН ==========
BOT_TOKEN = "8740387123:AAHET8K33FpV0XRAAu2rIubP3zM4qTA01Yk"
DATA_FILE = "user_data.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== ХРАНИЛИЩЕ ==========
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_data = load_data()

# ========== ФУНКЦИЯ ДЛЯ ПРОВЕРКИ/СОЗДАНИЯ ПОЛЬЗОВАТЕЛЯ ==========
def ensure_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "items": [],
            "sales": [],
            "money": {"salary": 0, "turnover": 0, "post": 0, "pillow": 0, "dream": 0},
            "item_counter": 1
        }
        save_data(user_data)
        return True
    return False

# ========== ФУНКЦИЯ ДЛЯ ПЕРЕСЧЁТА КОНВЕРТОВ ==========
def recalculate_money(user_id):
    """Пересчитывает деньги из всех продаж заново"""
    sales = user_data[user_id].get("sales", [])
    money = {"salary": 0, "turnover": 0, "post": 0, "pillow": 0, "dream": 0}
    for sale in sales:
        price = sale.get("price", 0)
        money["salary"] += int(price * 0.3)
        money["turnover"] += int(price * 0.4)
        money["post"] += int(price * 0.15)
        money["pillow"] += int(price * 0.1)
        money["dream"] += int(price * 0.05)
    user_data[user_id]["money"] = money

# ========== БИБЛИОТЕКА ПРОМТОВ ==========
PROMPTS = {
    "dress": {"name": "👗 Платье", "text": """Professional fashion photography. A beautiful women's dress perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, folds, fabric texture, and colors exactly as they are. All tags and labels must remain inside the garment, not visible on the front. Soft diffused studio lighting. 8k, hyper-realistic, commercial catalog quality, sharp focus on fabric and details."""},
    "coat": {"name": "🧥 Пальто/Куртка", "text": """Professional outerwear photography. A stylish coat perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, draping, fabric texture, and colors. Internal labels must remain hidden inside the garment. Soft diffused lighting. 8k, hyper-realistic, luxury catalog quality."""},
    "pants": {"name": "👖 Джинсы/Брюки", "text": """Professional product photography. A pair of pants perfectly displayed on a minimalist white mannequin. Pure white studio background. Keep the original fit, folds, denim texture, and colors. Tags and labels must stay inside. Soft studio lighting. 8k, sharp focus, commercial quality."""},
    "sweater": {"name": "👚 Кофта/Свитер", "text": """Professional knitwear photography. A cozy sweater perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the original shape, knit texture, drape, and colors. Labels must remain hidden inside. Soft natural lighting. 8k, hyper-realistic, commercial quality."""},
    "shirt": {"name": "👕 Рубашка/Блузка", "text": """Professional shirt photography. A crisp shirt perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the original shape, collar, cuffs, fabric texture, and colors. Tags must stay inside. Bright studio lighting. 8k, sharp focus, commercial catalog quality."""},
    "short": {"name": "🩳 Шорты/Юбка", "text": """Professional bottom wear photography. A stylish skirt/shorts perfectly displayed on a minimalist white mannequin. Pure white studio background. Keep the original shape, draping, fabric texture, and colors. Labels must remain inside. Soft diffused lighting. 8k, commercial quality."""},
    "default": {"name": "👔 Другое", "text": """Professional product photography. The garment perfectly displayed on a minimalist white mannequin. Pure white studio background. Keep the original shape, fabric texture, colors, and all details. All tags and labels must remain hidden inside. Soft studio lighting. 8k, hyper-realistic, commercial catalog quality."""}
}

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 План на сегодня", callback_data="strategy")],
        [InlineKeyboardButton(text="💰 Добавить продажу", callback_data="sale")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📸 Мои вещи", callback_data="items")],
        [InlineKeyboardButton(text="➕ Добавить вещь", callback_data="add_item_menu")],
        [InlineKeyboardButton(text="🔍 Поиск вещи", callback_data="search_item")],
        [InlineKeyboardButton(text="🗣 Готовые фразы", callback_data="scripts")],
        [InlineKeyboardButton(text="🎨 Получить промт", callback_data="prompt_menu")],
        [InlineKeyboardButton(text="🏆 Топ продаж", callback_data="top_sales")]
    ])
    return kb

def back_to_menu_button():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")]
    ])
    return kb

def back_button(callback_data):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 На шаг назад", callback_data=callback_data)]
    ])
    return kb

def prompt_category_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👗 Платье", callback_data="prompt_dress")],
        [InlineKeyboardButton(text="🧥 Пальто/Куртка", callback_data="prompt_coat")],
        [InlineKeyboardButton(text="👖 Джинсы/Брюки", callback_data="prompt_pants")],
        [InlineKeyboardButton(text="👚 Кофта/Свитер", callback_data="prompt_sweater")],
        [InlineKeyboardButton(text="👕 Рубашка/Блузка", callback_data="prompt_shirt")],
        [InlineKeyboardButton(text="🩳 Шорты/Юбка", callback_data="prompt_short")],
        [InlineKeyboardButton(text="👔 Другое", callback_data="prompt_default")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")]
    ])
    return kb

def item_actions_menu(item_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_item_{item_id}")],
        [InlineKeyboardButton(text="❌ Удалить вещь", callback_data=f"delete_item_{item_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_items")]
    ])
    return kb

def confirm_delete_menu(item_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{item_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel_delete_{item_id}")]
    ])
    return kb

# ========== СОСТОЯНИЯ ==========
class ItemForm(StatesGroup):
    photo = State()
    name = State()
    size = State()
    color = State()
    category = State()
    tags = State()
    price = State()

class EditForm(StatesGroup):
    item_id = State()
    field = State()
    value = State()

class SaleForm(StatesGroup):
    item_id = State()
    price = State()

class SearchForm(StatesGroup):
    query = State()

# ========== НАПОМИНАНИЯ ==========
async def check_reminders():
    last_morning = None
    last_evening = None
    MORNING_MESSAGES = ["🌅 Доброе утро! Сегодня отличный день для продаж! 📸 Сфоткай 5 вещей и выложи на Авито.", "🌞 Вставай, мама! Новая партия ждёт своего покупателя. Сегодня цель — 3 продажи! 💪", "☀️ Утро начинается с плана: 5 фото, 5 объявлений, 5 ответов покупателям. Ты справишься! 🚀"]
    EVENING_MESSAGES = ["🌙 Отличная работа сегодня! Проверь сообщения и обнови объявления. Завтра будет новый день! 🌟", "🌙 День закончен. Посчитай продажи и запиши их в бота. Отдыхай, ты заслужила! 💤", "🌙 Время подводить итоги! Сколько вещей продала сегодня? Не забудь обновить объявления! 📊"]
    
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        if current_time == "09:00" and last_morning != now.strftime("%d.%m.%Y"):
            last_morning = now.strftime("%d.%m.%Y")
            for user_id in user_data.keys():
                try:
                    await bot.send_message(user_id, random.choice(MORNING_MESSAGES), parse_mode="HTML")
                except:
                    pass
        if current_time == "19:00" and last_evening != now.strftime("%d.%m.%Y"):
            last_evening = now.strftime("%d.%m.%Y")
            for user_id in user_data.keys():
                try:
                    sales_today = len([s for s in user_data[user_id].get("sales", []) if s.get("date") == datetime.now().strftime("%d.%m.%Y")])
                    msg = random.choice(EVENING_MESSAGES)
                    await bot.send_message(user_id, f"{msg}\n\n📊 Продано сегодня: {sales_today} вещей", parse_mode="HTML")
                except:
                    pass
        await asyncio.sleep(30)

# ========== СТАРТ ==========
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    await message.answer(
        "👋 Мама, я твой умный бизнес-секретарь!\n"
        "Я помню каждую вещь, считаю деньги, напоминаю о планах и даю готовые промты для фото на манекене.\n\n"
        "⬇️ Выбери действие:",
        reply_markup=main_menu()
    )

# ========== НАЗАД В ГЛАВНОЕ МЕНЮ ==========
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("👋 Главное меню:\n\n⬇️ Выбери действие:", reply_markup=main_menu())
    await callback.answer()

# ========== СТРАТЕГИЯ ==========
@dp.callback_query(lambda c: c.data == "strategy")
async def show_strategy(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    sales = user_data.get(user_id, {}).get("sales", [])
    sales_today = len([s for s in sales if s.get("date") == datetime.now().strftime("%d.%m.%Y")])
    text = (f"📅 <b>План на сегодня</b>\n\n✅ Продано сегодня: {sales_today} / 3\n\n📋 <b>Чек-лист:</b>\n1️⃣ Сфотографируй 5 вещей\n2️⃣ Выложи их на Авито в 19:00\n3️⃣ Обнови 10 старых объявлений\n4️⃣ Ответь на все сообщения\n5️⃣ Добавь все продажи в бота\n\n🔥 <b>Совет:</b> Если вещь не продаётся 2 недели — отдай за 199 ₽")
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_menu_button())
    await callback.answer()

# ========== ПРОМТЫ ==========
@dp.callback_query(lambda c: c.data == "prompt_menu")
async def prompt_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer(
        "🎨 <b>Выбери категорию вещи</b>\n\nЯ выдам готовый промт для генерации фото на манекене.\nПросто скопируй его и вставь в Nano Banana / любую нейросеть.\n\n⬇️ Выбери категорию:",
        parse_mode="HTML",
        reply_markup=prompt_category_menu()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("prompt_"))
async def prompt_category_selected(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    category_map = {"prompt_dress": "dress", "prompt_coat": "coat", "prompt_pants": "pants", "prompt_sweater": "sweater", "prompt_shirt": "shirt", "prompt_short": "short", "prompt_default": "default"}
    category_key = category_map.get(callback.data, "default")
    prompt_data = PROMPTS.get(category_key, PROMPTS["default"])
    await callback.message.delete()
    await callback.message.answer(
        f"🎨 <b>Промт для {prompt_data['name']}</b>\n\n<b>⬇️ Скопируй этот текст:</b>\n<code>{prompt_data['text']}</code>\n\n📌 <b>Инструкция:</b>\n1️⃣ Скопируй текст выше\n2️⃣ Вставь в нейросеть (Nano Banana, Midjourney, Kandinsky)\n3️⃣ Загрузи своё фото вещи\n4️⃣ Нажми «Сгенерировать»\n\n✨ Получишь профессиональное фото на манекене!",
        parse_mode="HTML",
        reply_markup=back_to_menu_button()
    )
    await callback.answer()

# ========== ТОП ПРОДАЖ ==========
@dp.callback_query(lambda c: c.data == "top_sales")
async def show_top_sales(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    sales = user_data.get(user_id, {}).get("sales", [])
    if not sales:
        text = "🏆 Ты пока ничего не продала. Добавь первую продажу через кнопку «💰 Добавить продажу»"
    else:
        items_count = {}
        for sale in sales:
            name = sale.get("name", "Без названия")
            items_count[name] = items_count.get(name, 0) + 1
        sorted_items = sorted(items_count.items(), key=lambda x: x[1], reverse=True)[:5]
        text = "🏆 <b>Твои лучшие вещи (по частоте продаж):</b>\n\n"
        for i, (name, count) in enumerate(sorted_items, 1):
            text += f"{i}. {name} — {count} шт.\n"
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_menu_button())
    await callback.answer()

# ========== ДОБАВЛЕНИЕ ВЕЩИ ==========
@dp.callback_query(lambda c: c.data == "add_item_menu")
async def add_item_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer(
        "📸 <b>Добавляем новую вещь</b>\n\nОтправь мне <b>фото</b> вещи (одно фото).",
        parse_mode="HTML",
        reply_markup=back_to_menu_button()
    )
    await state.set_state(ItemForm.photo)
    await callback.answer()

@dp.message(ItemForm.photo, F.photo)
async def item_photo(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await message.answer(
        "📝 Напиши <b>название</b> вещи (например: Платье летнее):",
        parse_mode="HTML",
        reply_markup=back_button("add_item_menu")
    )
    await state.set_state(ItemForm.name)

@dp.message(ItemForm.name)
async def item_name(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    await state.update_data(name=message.text)
    await message.answer(
        "📏 Напиши <b>размер</b> (46, M, L):",
        parse_mode="HTML",
        reply_markup=back_button("item_back_to_name")
    )
    await state.set_state(ItemForm.size)

@dp.message(ItemForm.size)
async def item_size(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    await state.update_data(size=message.text)
    await message.answer(
        "🎨 Напиши <b>цвет</b>:",
        parse_mode="HTML",
        reply_markup=back_button("item_back_to_size")
    )
    await state.set_state(ItemForm.color)

@dp.message(ItemForm.color)
async def item_color(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    await state.update_data(color=message.text)
    await message.answer(
        "🏷️ Напиши <b>категорию</b> (Платья, Кофты, Джинсы, Шорты, Куртки):",
        parse_mode="HTML",
        reply_markup=back_button("item_back_to_color")
    )
    await state.set_state(ItemForm.category)

@dp.message(ItemForm.category)
async def item_category(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    await state.update_data(category=message.text)
    await message.answer(
        "🏷️ Напиши <b>теги</b> (например: летнее, офис, праздник).\nМожно перечислить через запятую. Если не хочешь — напиши «нет».",
        parse_mode="HTML",
        reply_markup=back_button("item_back_to_category")
    )
    await state.set_state(ItemForm.tags)

@dp.message(ItemForm.tags)
async def item_tags(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    tags = message.text.strip()
    if tags.lower() == "нет":
        tags = ""
    await state.update_data(tags=tags)
    await message.answer(
        "💰 Напиши <b>цену</b> (число):",
        parse_mode="HTML",
        reply_markup=back_button("item_back_to_tags")
    )
    await state.set_state(ItemForm.price)

@dp.message(ItemForm.price)
async def save_item(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    try:
        price = int(message.text)
        data = await state.get_data()
        
        item_id = user_data[user_id]["item_counter"]
        user_data[user_id]["item_counter"] += 1
        user_data[user_id]["items"].append({
            "id": item_id,
            "name": data.get("name"),
            "size": data.get("size"),
            "color": data.get("color"),
            "category": data.get("category"),
            "tags": data.get("tags", ""),
            "price": price,
            "photo": data.get("photo"),
            "status": "active",
            "created": datetime.now().strftime("%d.%m.%Y")
        })
        save_data(user_data)
        await message.answer_photo(
            data.get("photo"),
            caption=(
                f"✅ <b>Вещь добавлена!</b>\n\n"
                f"🆔 <b>ID:</b> {item_id}\n"
                f"📦 {data.get('name')}\n"
                f"📏 Размер: {data.get('size')}\n"
                f"🎨 Цвет: {data.get('color')}\n"
                f"🏷️ Категория: {data.get('category')}\n"
                f"🏷️ Теги: {data.get('tags') or 'нет'}\n"
                f"💰 Цена: {price} ₽"
            ),
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Ошибка! Введи число, например: 1200",
            reply_markup=back_button("item_back_to_price")
        )

# ========== ОБРАБОТЧИКИ ВОЗВРАТА НА ШАГ ПРИ ДОБАВЛЕНИИ ==========
@dp.callback_query(lambda c: c.data == "item_back_to_name")
async def back_to_name(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("📝 Напиши <b>название</b> вещи:", parse_mode="HTML", reply_markup=back_button("add_item_menu"))
    await state.set_state(ItemForm.name)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_size")
async def back_to_size(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("📏 Напиши <b>размер</b> (46, M, L):", parse_mode="HTML", reply_markup=back_button("item_back_to_name"))
    await state.set_state(ItemForm.size)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_color")
async def back_to_color(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("🎨 Напиши <b>цвет</b>:", parse_mode="HTML", reply_markup=back_button("item_back_to_size"))
    await state.set_state(ItemForm.color)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_category")
async def back_to_category(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("🏷️ Напиши <b>категорию</b> (Платья, Кофты, Джинсы, Шорты, Куртки):", parse_mode="HTML", reply_markup=back_button("item_back_to_color"))
    await state.set_state(ItemForm.category)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_tags")
async def back_to_tags(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("🏷️ Напиши <b>теги</b> (например: летнее, офис, праздник).\nМожно перечислить через запятую. Если не хочешь — напиши «нет».", parse_mode="HTML", reply_markup=back_button("item_back_to_category"))
    await state.set_state(ItemForm.tags)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_price")
async def back_to_price(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("💰 Напиши <b>цену</b> (число):", parse_mode="HTML", reply_markup=back_button("item_back_to_tags"))
    await state.set_state(ItemForm.price)
    await callback.answer()

# ========== РЕДАКТИРОВАНИЕ ВЕЩИ ==========
@dp.callback_query(lambda c: c.data.startswith("edit_item_"))
async def edit_item_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    items = user_data.get(user_id, {}).get("items", [])
    item = next((i for i in items if i.get("id") == item_id), None)
    
    if not item:
        await callback.message.delete()
        await callback.message.answer("❌ Вещь не найдена.", reply_markup=back_to_menu_button())
        await callback.answer()
        return
    
    await state.update_data(item_id=item_id)
    await callback.message.delete()
    await callback.message.answer(
        f"✏️ <b>Редактирование вещи</b>\n\n"
        f"🆔 ID: {item['id']}\n"
        f"📦 {item['name']}\n"
        f"📏 Размер: {item['size']}\n"
        f"🎨 Цвет: {item['color']}\n"
        f"🏷️ Категория: {item['category']}\n"
        f"🏷️ Теги: {item.get('tags', 'нет')}\n"
        f"💰 Цена: {item['price']} ₽\n"
        f"📌 Статус: {item.get('status', 'активна')}\n\n"
        "⬇️ Выбери, что хочешь изменить:",
        parse_mode="HTML",
        reply_markup=edit_item_menu(item_id)
    )
    await callback.answer()

def edit_item_menu(item_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить название", callback_data=f"edit_name_{item_id}")],
        [InlineKeyboardButton(text="📏 Изменить размер", callback_data=f"edit_size_{item_id}")],
        [InlineKeyboardButton(text="🎨 Изменить цвет", callback_data=f"edit_color_{item_id}")],
        [InlineKeyboardButton(text="🏷️ Изменить категорию", callback_data=f"edit_category_{item_id}")],
        [InlineKeyboardButton(text="🏷️ Изменить теги", callback_data=f"edit_tags_{item_id}")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"edit_price_{item_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_items")]
    ])
    return kb

@dp.callback_query(lambda c: c.data.startswith("edit_name_"))
async def edit_name_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    await state.update_data(item_id=item_id, field="name")
    await callback.message.delete()
    await callback.message.answer("📝 Напиши <b>новое название</b> для вещи:", parse_mode="HTML", reply_markup=back_button(f"edit_item_{item_id}"))
    await state.set_state(EditForm.value)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("edit_size_"))
async def edit_size_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    await state.update_data(item_id=item_id, field="size")
    await callback.message.delete()
    await callback.message.answer("📏 Напиши <b>новый размер</b> (46, M, L):", parse_mode="HTML", reply_markup=back_button(f"edit_item_{item_id}"))
    await state.set_state(EditForm.value)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("edit_color_"))
async def edit_color_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    await state.update_data(item_id=item_id, field="color")
    await callback.message.delete()
    await callback.message.answer("🎨 Напиши <b>новый цвет</b>:", parse_mode="HTML", reply_markup=back_button(f"edit_item_{item_id}"))
    await state.set_state(EditForm.value)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("edit_category_"))
async def edit_category_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    await state.update_data(item_id=item_id, field="category")
    await callback.message.delete()
    await callback.message.answer("🏷️ Напиши <b>новую категорию</b> (Платья, Кофты, Джинсы, Шорты, Куртки):", parse_mode="HTML", reply_markup=back_button(f"edit_item_{item_id}"))
    await state.set_state(EditForm.value)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("edit_tags_"))
async def edit_tags_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    await state.update_data(item_id=item_id, field="tags")
    await callback.message.delete()
    await callback.message.answer("🏷️ Напиши <b>новые теги</b> (через запятую). Если не хочешь — напиши «нет»:", parse_mode="HTML", reply_markup=back_button(f"edit_item_{item_id}"))
    await state.set_state(EditForm.value)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("edit_price_"))
async def edit_price_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    await state.update_data(item_id=item_id, field="price")
    await callback.message.delete()
    await callback.message.answer("💰 Напиши <b>новую цену</b> (число):", parse_mode="HTML", reply_markup=back_button(f"edit_item_{item_id}"))
    await state.set_state(EditForm.value)
    await callback.answer()

@dp.message(EditForm.value)
async def save_edit_value(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    data = await state.get_data()
    item_id = data.get("item_id")
    field = data.get("field")
    new_value = message.text.strip()
    
    items = user_data.get(user_id, {}).get("items", [])
    item = next((i for i in items if i.get("id") == item_id), None)
    
    if not item:
        await message.answer("❌ Вещь не найдена.", reply_markup=main_menu())
        await state.clear()
        return
    
    if field == "price":
        try:
            new_value = int(new_value)
        except ValueError:
            await message.answer("❌ Ошибка! Введи число.", reply_markup=back_button(f"edit_item_{item_id}"))
            return
    elif field == "tags":
        if new_value.lower() == "нет":
            new_value = ""
    
    item[field] = new_value
    save_data(user_data)
    
    await message.answer(
        f"✅ <b>Изменения сохранены!</b>\n\n"
        f"🆔 ID: {item['id']}\n"
        f"📦 {item['name']}\n"
        f"📏 Размер: {item['size']}\n"
        f"🎨 Цвет: {item['color']}\n"
        f"🏷️ Категория: {item['category']}\n"
        f"🏷️ Теги: {item.get('tags', 'нет')}\n"
        f"💰 Цена: {item['price']} ₽",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    await state.clear()

@dp.callback_query(lambda c: c.data == "back_to_items")
async def back_to_items(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await show_items(callback, state)

# ========== УДАЛЕНИЕ ВЕЩИ ==========
@dp.callback_query(lambda c: c.data.startswith("delete_item_"))
async def delete_item_confirm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    
    items = user_data.get(user_id, {}).get("items", [])
    item = next((i for i in items if i.get("id") == item_id), None)
    
    if not item:
        await callback.message.delete()
        await callback.message.answer("❌ Вещь не найдена.", reply_markup=back_to_menu_button())
        await callback.answer()
        return
    
    await callback.message.delete()
    await callback.message.answer(
        f"⚠️ <b>Ты уверена, что хочешь удалить вещь?</b>\n\n"
        f"🆔 ID: {item['id']}\n"
        f"📦 {item['name']}\n"
        f"💰 Цена: {item['price']} ₽\n"
        f"📌 Статус: {item.get('status', 'активна')}\n\n"
        f"Если по этой вещи были продажи — они тоже будут удалены, и деньги из конвертов вернутся.",
        parse_mode="HTML",
        reply_markup=confirm_delete_menu(item_id)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("confirm_delete_"))
async def confirm_delete_item(callback: CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    
    items = user_data.get(user_id, {}).get("items", [])
    item = next((i for i in items if i.get("id") == item_id), None)
    
    if not item:
        await callback.message.delete()
        await callback.message.answer("❌ Вещь не найдена.", reply_markup=back_to_menu_button())
        await callback.answer()
        return
    
    # Удаляем вещь
    user_data[user_id]["items"] = [i for i in items if i.get("id") != item_id]
    
    # Удаляем все продажи, связанные с этой вещью
    sales = user_data[user_id].get("sales", [])
    user_data[user_id]["sales"] = [s for s in sales if s.get("item_id") != item_id]
    
    # Пересчитываем деньги из оставшихся продаж
    recalculate_money(user_id)
    save_data(user_data)
    
    await callback.message.delete()
    await callback.message.answer(
        f"✅ <b>Вещь удалена!</b>\n\n"
        f"🆔 ID: {item['id']}\n"
        f"📦 {item['name']}\n\n"
        f"Все связанные продажи и их деньги убраны из статистики.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("cancel_delete_"))
async def cancel_delete_item(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("❌ Удаление отменено.", reply_markup=main_menu())
    await callback.answer()

# ========== МОИ ВЕЩИ ==========
@dp.callback_query(lambda c: c.data == "items")
async def show_items(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    items = user_data.get(user_id, {}).get("items", [])
    
    if not items:
        await callback.message.delete()
        await callback.message.answer("📸 У тебя пока нет вещей в базе.\n\nДобавь первую вещь через кнопку «➕ Добавить вещь»", reply_markup=back_to_menu_button())
        await callback.answer()
        return
    
    for item in items[-5:]:
        if item.get("photo"):
            status_emoji = "✅" if item.get("status") == "active" else "❌"
            caption = (f"{status_emoji} <b>ID:</b> {item['id']}\n📦 {item['name']}\n📏 Размер: {item['size']}\n🎨 Цвет: {item['color']}\n🏷️ {item['category']}\n🏷️ Теги: {item.get('tags', 'нет')}\n💰 {item['price']} ₽\n📅 {item.get('created', '')}")
            await callback.message.answer_photo(item['photo'], caption=caption, parse_mode="HTML", reply_markup=item_actions_menu(item['id']))
    
    total = len(items)
    active = len([i for i in items if i.get("status") == "active"])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📋 Все вещи ({total} шт.)", callback_data="items_list")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="search_item")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")]
    ])
    await callback.message.delete()
    await callback.message.answer(
        f"📸 <b>Последние добавленные вещи</b>\n"
        f"Всего: {total} | ✅ Активных: {active}\n\n"
        f"Что хочешь сделать дальше?",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "items_list")
async def show_items_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    items = user_data.get(user_id, {}).get("items", [])
    if not items:
        text = "📋 Пока нет ни одной вещи."
    else:
        active = [i for i in items if i.get("status") == "active"]
        sold = [i for i in items if i.get("status") == "sold"]
        text = f"📋 <b>Все вещи</b>\n\n✅ Активных: {len(active)}\n❌ Продано: {len(sold)}\n\n"
        for item in items[-30:]:
            status = "✅" if item.get("status") == "active" else "❌"
            text += f"{status} 🆔{item['id']} | {item['name']} | {item['size']} | {item.get('category', '')}\n"
        if len(items) > 30:
            text += f"\n...и ещё {len(items)-30} вещей. Используй поиск!"
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_menu_button())
    await callback.answer()

# ========== ПОИСК ==========
@dp.callback_query(lambda c: c.data == "search_item")
async def search_item_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("🔍 Напиши, что ищем:\n(Название, размер, цвет, категорию или тег)", reply_markup=back_to_menu_button())
    await state.set_state(SearchForm.query)
    await callback.answer()

@dp.message(SearchForm.query)
async def search_item_result(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    query = message.text.lower()
    items = user_data.get(user_id, {}).get("items", [])
    found = []
    for item in items:
        if (query in item.get("name", "").lower() or query in item.get("size", "").lower() or query in item.get("color", "").lower() or query in item.get("category", "").lower() or query in item.get("tags", "").lower()):
            found.append(item)
    if found:
        await message.answer(f"✅ Найдено {len(found)} вещей:")
        for item in found[:5]:
            if item.get("photo"):
                caption = f"🆔 {item['id']} | {item['name']} | {item['size']} | {item['price']} ₽"
                await message.answer_photo(item['photo'], caption=caption, reply_markup=item_actions_menu(item['id']))
        if len(found) > 5:
            await message.answer(f"...и ещё {len(found)-5} вещей. Уточни запрос для точного поиска.")
        await message.answer("🔍 Что-то ещё?", reply_markup=main_menu())
    else:
        await message.answer("❌ Ничего не найдено. Попробуй другой запрос.", reply_markup=main_menu())
    await state.clear()

# ========== ПРОДАЖА ==========
@dp.callback_query(lambda c: c.data == "sale")
async def start_sale(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("💰 Напиши <b>ID вещи</b>, которую продала.\nПосмотреть ID можно в разделе «Мои вещи».", parse_mode="HTML", reply_markup=back_to_menu_button())
    await state.set_state(SaleForm.item_id)
    await callback.answer()

@dp.message(SaleForm.item_id)
async def get_sale_price(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    try:
        item_id = int(message.text)
        items = user_data.get(user_id, {}).get("items", [])
        item = next((i for i in items if i.get("id") == item_id), None)
        if not item:
            await message.answer("❌ Вещь с таким ID не найдена. Попробуй ещё раз.", reply_markup=back_to_menu_button())
            return
        await state.update_data(item_id=item_id, item_name=item.get("name"), default_price=item.get("price"))
        await message.answer(
            f"📦 {item.get('name')}\n💰 Рекомендуемая цена: {item.get('price')} ₽\n\nНапиши <b>цену продажи</b> (число):",
            parse_mode="HTML",
            reply_markup=back_button("sale")
        )
        await state.set_state(SaleForm.price)
    except ValueError:
        await message.answer("❌ Введи число (ID вещи)", reply_markup=back_to_menu_button())

@dp.message(SaleForm.price)
async def save_sale(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    try:
        price = int(message.text)
        data = await state.get_data()
        item_id = data.get("item_id")
        item_name = data.get("item_name", "Без названия")
        
        user_data[user_id]["sales"].append({
            "item_id": item_id,
            "name": item_name,
            "price": price,
            "date": datetime.now().strftime("%d.%m.%Y")
        })
        for item in user_data[user_id]["items"]:
            if item.get("id") == item_id:
                item["status"] = "sold"
                break
        recalculate_money(user_id)
        save_data(user_data)
        
        await message.answer(
            f"✅ Продажа записана!\n\n🆔 Вещь #{item_id}\n📦 {item_name} — {price} ₽\n\n<b>Деньги разложены:</b>\n👩 Себе (30%): {int(price*0.3)} ₽\n📦 Оборот (40%): {int(price*0.4)} ₽\n📮 Почта (15%): {int(price*0.15)} ₽\n🛡️ Подушка (10%): {int(price*0.1)} ₽\n✨ Мечта (5%): {int(price*0.05)} ₽",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Ошибка! Введи число", reply_markup=back_to_menu_button())

# ========== СТАТИСТИКА (С КНОПКОЙ ОТМЕНЫ ПОСЛЕДНЕЙ ПРОДАЖИ) ==========
@dp.callback_query(lambda c: c.data == "stats")
async def show_stats(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    data = user_data.get(user_id, {})
    sales = data.get("sales", [])
    items = data.get("items", [])
    money = data.get("money", {})
    total_sales = len(sales)
    total_revenue = sum(s.get("price", 0) for s in sales)
    avg_price = int(total_revenue / total_sales) if total_sales > 0 else 0
    
    categories = {}
    for item in items:
        cat = item.get("category", "Другое")
        categories[cat] = categories.get(cat, 0) + 1
    cat_text = ""
    for cat, count in list(categories.items())[:5]:
        cat_text += f"{cat}: {count} шт.\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Отменить последнюю продажу", callback_data="undo_last_sale")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")]
    ])
    
    stats_text = (f"📊 <b>Твоя статистика</b>\n\n📦 Продано: {total_sales} шт.\n💰 Выручка: {total_revenue} ₽\n📈 Средний чек: {avg_price} ₽\n📸 Всего вещей: {len(items)} шт.\n\n<b>📂 Категории:</b>\n{cat_text or 'Пока нет'}\n<b>💰 Конверты:</b>\n👩 Себе: {money.get('salary', 0)} ₽\n📦 Оборот: {money.get('turnover', 0)} ₽\n📮 Почта: {money.get('post', 0)} ₽\n🛡️ Подушка: {money.get('pillow', 0)} ₽\n✨ Мечта: {money.get('dream', 0)} ₽")
    await callback.message.delete()
    await callback.message.answer(stats_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

# ========== ОТМЕНА ПОСЛЕДНЕЙ ПРОДАЖИ ==========
@dp.callback_query(lambda c: c.data == "undo_last_sale")
async def undo_last_sale(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    sales = user_data.get(user_id, {}).get("sales", [])
    
    if not sales:
        await callback.message.delete()
        await callback.message.answer("❌ Нет продаж, которые можно отменить.", reply_markup=back_to_menu_button())
        await callback.answer()
        return
    
    last_sale = sales[-1]
    item_id = last_sale.get("item_id")
    item_name = last_sale.get("name", "Без названия")
    price = last_sale.get("price", 0)
    
    # Удаляем последнюю продажу
    user_data[user_id]["sales"] = sales[:-1]
    
    # Возвращаем вещь в активные (если она ещё есть в списке)
    for item in user_data[user_id]["items"]:
        if item.get("id") == item_id:
            item["status"] = "active"
            break
    
    # Пересчитываем деньги
    recalculate_money(user_id)
    save_data(user_data)
    
    await callback.message.delete()
    await callback.message.answer(
        f"↩️ <b>Продажа отменена!</b>\n\n"
        f"🆔 Вещь #{item_id}\n"
        f"📦 {item_name}\n"
        f"💰 {price} ₽\n\n"
        f"Вещь возвращена в статус «активна».\n"
        f"Деньги из этой продажи убраны из конвертов.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    await callback.answer()

# ========== СКРИПТЫ ==========
@dp.callback_query(lambda c: c.data == "scripts")
async def show_scripts(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    ensure_user(user_id)
    text = ("🗣 <b>Готовые фразы для общения с покупателями</b>\n\n1️⃣ <b>Если просят скидку:</b>\n«Честно, я уже поставила минимум. Но если оформите сегодня — положу в подарок шарфик!»\n\n2️⃣ <b>Если говорят «Подумаю»:</b>\n«Понимаю! Такие вещи быстро уходят. Отложу до вечера, потом уйдёт другому.»\n\n3️⃣ <b>Чтобы привести подругу:</b>\n«Забирайте, и если приведете соседку — скидка 30% на следующую вещь!»\n\n4️⃣ <b>Закрытие сделки:</b>\n«Посылка у вас! Если всё понравилось — оставьте отзыв. Заходите ещё!»")
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_menu_button())
    await callback.answer()

# ========== ЗАПУСК ==========
async def main():
    print("✅ Бот с удалением и отменой продаж запущен!")
    asyncio.create_task(check_reminders())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
