import asyncio
import logging
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ========== ТОКЕН ==========
BOT_TOKEN = "8740387123:AAHET8K33FpV0XRAAu2rIubP3zM4qTA01Yk"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}

# ========== БИБЛИОТЕКА ПРОМТОВ ==========
PROMPTS = {
    "dress": {
        "name": "👗 Платье",
        "text": """Professional fashion photography. A beautiful women's dress perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, folds, fabric texture, and colors exactly as they are. All tags and labels must remain inside the garment, not visible on the front. Soft diffused studio lighting. 8k, hyper-realistic, commercial catalog quality, sharp focus on fabric and details."""
    },
    "coat": {
        "name": "🧥 Пальто/Куртка",
        "text": """Professional outerwear photography. A stylish coat perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, draping, fabric texture, and colors. Internal labels must remain hidden inside the garment. Soft diffused lighting. 8k, hyper-realistic, luxury catalog quality."""
    },
    "pants": {
        "name": "👖 Джинсы/Брюки",
        "text": """Professional product photography. A pair of pants perfectly displayed on a minimalist white mannequin. Pure white studio background. Keep the original fit, folds, denim texture, and colors. Tags and labels must stay inside. Soft studio lighting. 8k, sharp focus, commercial quality."""
    },
    "sweater": {
        "name": "👚 Кофта/Свитер",
        "text": """Professional knitwear photography. A cozy sweater perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the original shape, knit texture, drape, and colors. Labels must remain hidden inside. Soft natural lighting. 8k, hyper-realistic, commercial quality."""
    },
    "shirt": {
        "name": "👕 Рубашка/Блузка",
        "text": """Professional shirt photography. A crisp shirt perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the original shape, collar, cuffs, fabric texture, and colors. Tags must stay inside. Bright studio lighting. 8k, sharp focus, commercial catalog quality."""
    },
    "short": {
        "name": "🩳 Шорты/Юбка",
        "text": """Professional bottom wear photography. A stylish skirt/shorts perfectly displayed on a minimalist white mannequin. Pure white studio background. Keep the original shape, draping, fabric texture, and colors. Labels must remain inside. Soft diffused lighting. 8k, commercial quality.""",
    },
    "default": {
        "name": "👔 Другое",
        "text": """Professional product photography. The garment perfectly displayed on a minimalist white mannequin. Pure white studio background. Keep the original shape, fabric texture, colors, and all details. All tags and labels must remain hidden inside. Soft studio lighting. 8k, hyper-realistic, commercial catalog quality."""
    }
}

# ========== ГЛАВНОЕ МЕНЮ ==========
def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 План на сегодня", callback_data="strategy")],
        [InlineKeyboardButton(text="💰 Добавить продажу", callback_data="sale")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📸 Мои вещи", callback_data="items")],
        [InlineKeyboardButton(text="➕ Добавить вещь", callback_data="add_item_menu")],
        [InlineKeyboardButton(text="🔍 Поиск вещи", callback_data="search_item")],
        [InlineKeyboardButton(text="🗣 Готовые фразы", callback_data="scripts")],
        [InlineKeyboardButton(text="🎨 Получить промт для манекена", callback_data="prompt_menu")]
    ])
    return kb

def back_button():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    return kb

def dialog_back_button(callback_data):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
    ])
    return kb

# ========== КЛАВИАТУРА ДЛЯ ВЫБОРА КАТЕГОРИИ ПРОМТА ==========
def prompt_category_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👗 Платье", callback_data="prompt_dress")],
        [InlineKeyboardButton(text="🧥 Пальто/Куртка", callback_data="prompt_coat")],
        [InlineKeyboardButton(text="👖 Джинсы/Брюки", callback_data="prompt_pants")],
        [InlineKeyboardButton(text="👚 Кофта/Свитер", callback_data="prompt_sweater")],
        [InlineKeyboardButton(text="👕 Рубашка/Блузка", callback_data="prompt_shirt")],
        [InlineKeyboardButton(text="🩳 Шорты/Юбка", callback_data="prompt_short")],
        [InlineKeyboardButton(text="👔 Другое", callback_data="prompt_default")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    return kb

# ========== СОСТОЯНИЯ ==========
class ItemForm(StatesGroup):
    photo = State()
    name = State()
    size = State()
    color = State()
    category = State()
    price = State()

class SaleForm(StatesGroup):
    item_id = State()
    price = State()

class SearchForm(StatesGroup):
    query = State()

# ========== НАПОМИНАНИЯ ==========
async def check_reminders():
    last_morning = None
    last_evening = None
    
    MORNING_MESSAGES = [
        "🌅 Доброе утро! Сегодня отличный день для продаж! 📸 Сфоткай 5 вещей и выложи на Авито.",
        "🌞 Вставай, мама! Новая партия ждёт своего покупателя. Сегодня цель — 3 продажи! 💪",
        "☀️ Утро начинается с плана: 5 фото, 5 объявлений, 5 ответов покупателям. Ты справишься! 🚀"
    ]
    
    EVENING_MESSAGES = [
        "🌙 Отличная работа сегодня! Проверь сообщения и обнови объявления. Завтра будет новый день! 🌟",
        "🌙 День закончен. Посчитай продажи и запиши их в бота. Отдыхай, ты заслужила! 💤",
        "🌙 Время подводить итоги! Сколько вещей продала сегодня? Не забудь обновить объявления! 📊"
    ]
    
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
                    sales_today = len([s for s in user_data[user_id].get("sales", []) 
                                      if s.get("date") == datetime.now().strftime("%d.%m.%Y")])
                    msg = random.choice(EVENING_MESSAGES)
                    await bot.send_message(
                        user_id,
                        f"{msg}\n\n📊 Продано сегодня: {sales_today} вещей",
                        parse_mode="HTML"
                    )
                except:
                    pass
        
        await asyncio.sleep(30)

# ========== /start ==========
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {
            "items": [],
            "sales": [],
            "money": {"salary": 0, "turnover": 0, "post": 0, "pillow": 0, "dream": 0},
            "item_counter": 1
        }
    await message.answer(
        "👋 Мама, я твой умный бизнес-секретарь!\n"
        "Я помню каждую вещь, считаю деньги, напоминаю о планах и даю готовые промты для фото на манекене.\n\n"
        "⬇️ Выбери действие:",
        reply_markup=main_menu()
    )

# ========== НАЗАД В МЕНЮ ==========
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "👋 Главное меню:\n\n⬇️ Выбери действие:",
        reply_markup=main_menu()
    )
    await callback.answer()

# ========== СТРАТЕГИЯ ==========
@dp.callback_query(lambda c: c.data == "strategy")
async def show_strategy(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    sales = user_data.get(str(callback.from_user.id), {}).get("sales", [])
    sales_today = len([s for s in sales if s.get("date") == datetime.now().strftime("%d.%m.%Y")])
    
    text = (
        f"📅 <b>План на сегодня</b>\n\n"
        f"✅ Продано сегодня: {sales_today} / 3\n\n"
        "📋 <b>Чек-лист:</b>\n"
        "1️⃣ Сфотографируй 5 вещей\n"
        "2️⃣ Выложи их на Авито в 19:00\n"
        "3️⃣ Обнови 10 старых объявлений\n"
        "4️⃣ Ответь на все сообщения\n"
        "5️⃣ Добавь все продажи в бота\n\n"
        "🔥 <b>Совет:</b> Если вещь не продаётся 2 недели — отдай за 199 ₽"
    )
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button())
    await callback.answer()

# ========== ПОЛУЧЕНИЕ ПРОМТА ==========
@dp.callback_query(lambda c: c.data == "prompt_menu")
async def prompt_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "🎨 <b>Выбери категорию вещи</b>\n\n"
        "Я выдам готовый промт для генерации фото на манекене.\n"
        "Просто скопируй его и вставь в Nano Banana / Midjourney / любую нейросеть.\n\n"
        "⬇️ Выбери категорию:",
        parse_mode="HTML",
        reply_markup=prompt_category_menu()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("prompt_"))
async def prompt_category_selected(callback: CallbackQuery, state: FSMContext):
    category_map = {
        "prompt_dress": "dress",
        "prompt_coat": "coat",
        "prompt_pants": "pants",
        "prompt_sweater": "sweater",
        "prompt_shirt": "shirt",
        "prompt_short": "short",
        "prompt_default": "default"
    }
    
    category_key = category_map.get(callback.data, "default")
    prompt_data = PROMPTS.get(category_key, PROMPTS["default"])
    
    await callback.message.delete()
    await callback.message.answer(
        f"🎨 <b>Промт для {prompt_data['name']}</b>\n\n"
        f"<b>⬇️ Скопируй этот текст:</b>\n"
        f"<code>{prompt_data['text']}</code>\n\n"
        "📌 <b>Инструкция:</b>\n"
        "1️⃣ Скопируй текст выше\n"
        "2️⃣ Вставь в нейросеть (Nano Banana, Midjourney, Kandinsky)\n"
        "3️⃣ Загрузи своё фото вещи\n"
        "4️⃣ Нажми «Сгенерировать»\n\n"
        "✨ Получишь профессиональное фото на манекене!",
        parse_mode="HTML",
        reply_markup=back_button()
    )
    await callback.answer()

# ========== ДОБАВЛЕНИЕ ВЕЩИ ==========
@dp.callback_query(lambda c: c.data == "add_item_menu")
async def add_item_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "📸 <b>Добавляем новую вещь</b>\n\n"
        "Отправь мне <b>фото</b> вещи (одно фото).",
        parse_mode="HTML",
        reply_markup=back_button()
    )
    await state.set_state(ItemForm.photo)
    await callback.answer()

@dp.message(ItemForm.photo, F.photo)
async def item_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await message.answer(
        "📝 Напиши <b>название</b> вещи (например: Платье летнее):",
        parse_mode="HTML",
        reply_markup=dialog_back_button("add_item_menu")
    )
    await state.set_state(ItemForm.name)

@dp.message(ItemForm.name)
async def item_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "📏 Напиши <b>размер</b> (46, M, L):",
        parse_mode="HTML",
        reply_markup=dialog_back_button("item_back_to_name")
    )
    await state.set_state(ItemForm.size)

@dp.message(ItemForm.size)
async def item_size(message: Message, state: FSMContext):
    await state.update_data(size=message.text)
    await message.answer(
        "🎨 Напиши <b>цвет</b>:",
        parse_mode="HTML",
        reply_markup=dialog_back_button("item_back_to_size")
    )
    await state.set_state(ItemForm.color)

@dp.message(ItemForm.color)
async def item_color(message: Message, state: FSMContext):
    await state.update_data(color=message.text)
    await message.answer(
        "🏷️ Напиши <b>категорию</b> (Платья, Кофты, Джинсы, Шорты, Куртки):",
        parse_mode="HTML",
        reply_markup=dialog_back_button("item_back_to_color")
    )
    await state.set_state(ItemForm.category)

@dp.message(ItemForm.category)
async def item_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer(
        "💰 Напиши <b>цену</b> (число):",
        parse_mode="HTML",
        reply_markup=dialog_back_button("item_back_to_category")
    )
    await state.set_state(ItemForm.price)

@dp.message(ItemForm.price)
async def save_item(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        data = await state.get_data()
        user_id = str(message.from_user.id)
        
        item_id = user_data[user_id]["item_counter"]
        user_data[user_id]["item_counter"] += 1
        
        user_data[user_id]["items"].append({
            "id": item_id,
            "name": data.get("name"),
            "size": data.get("size"),
            "color": data.get("color"),
            "category": data.get("category"),
            "price": price,
            "photo": data.get("photo"),
            "status": "active",
            "created": datetime.now().strftime("%d.%m.%Y")
        })
        
        await message.answer_photo(
            data.get("photo"),
            caption=(
                f"✅ <b>Вещь добавлена!</b>\n\n"
                f"🆔 <b>ID:</b> {item_id}\n"
                f"📦 {data.get('name')}\n"
                f"📏 Размер: {data.get('size')}\n"
                f"🎨 Цвет: {data.get('color')}\n"
                f"🏷️ Категория: {data.get('category')}\n"
                f"💰 Цена: {price} ₽"
            ),
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Ошибка! Введи число, например: 1200",
            reply_markup=dialog_back_button("item_back_to_price")
        )

# ========== ОБРАБОТЧИКИ ВОЗВРАТА НА ШАГ ==========
@dp.callback_query(lambda c: c.data == "item_back_to_name")
async def back_to_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "📝 Напиши <b>название</b> вещи:",
        parse_mode="HTML",
        reply_markup=dialog_back_button("add_item_menu")
    )
    await state.set_state(ItemForm.name)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_size")
async def back_to_size(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "📏 Напиши <b>размер</b> (46, M, L):",
        parse_mode="HTML",
        reply_markup=dialog_back_button("item_back_to_name")
    )
    await state.set_state(ItemForm.size)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_color")
async def back_to_color(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "🎨 Напиши <b>цвет</b>:",
        parse_mode="HTML",
        reply_markup=dialog_back_button("item_back_to_size")
    )
    await state.set_state(ItemForm.color)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_category")
async def back_to_category(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "🏷️ Напиши <b>категорию</b> (Платья, Кофты, Джинсы, Шорты, Куртки):",
        parse_mode="HTML",
        reply_markup=dialog_back_button("item_back_to_color")
    )
    await state.set_state(ItemForm.category)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_price")
async def back_to_price(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "💰 Напиши <b>цену</b> (число):",
        parse_mode="HTML",
        reply_markup=dialog_back_button("item_back_to_category")
    )
    await state.set_state(ItemForm.price)
    await callback.answer()

# ========== МОИ ВЕЩИ ==========
@dp.callback_query(lambda c: c.data == "items")
async def show_items(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    items = user_data.get(user_id, {}).get("items", [])
    
    if not items:
        text = "📸 У тебя пока нет вещей в базе.\n\nДобавь первую вещь через кнопку «➕ Добавить вещь»"
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=back_button())
        await callback.answer()
        return
    
    for item in items[-5:]:
        if item.get("photo"):
            caption = (
                f"🆔 <b>ID:</b> {item['id']}\n"
                f"📦 {item['name']}\n"
                f"📏 Размер: {item['size']}\n"
                f"🎨 Цвет: {item['color']}\n"
                f"🏷️ {item['category']}\n"
                f"💰 {item['price']} ₽\n"
                f"📅 {item.get('created', '')}\n"
                f"📌 {item.get('status', 'активна')}"
            )
            await callback.message.answer_photo(item['photo'], caption=caption, parse_mode="HTML")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все вещи (списком)", callback_data="items_list")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="search_item")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    await callback.message.delete()
    await callback.message.answer(
        "📸 Последние добавленные вещи показаны выше.\n"
        "Что хочешь сделать дальше?",
        reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "items_list")
async def show_items_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    items = user_data.get(user_id, {}).get("items", [])
    
    text = "📋 <b>Все вещи</b>\n\n"
    for item in items[-20:]:
        status = "✅" if item.get("status") == "active" else "❌"
        text += f"{status} 🆔{item['id']} | {item['name']} | {item['size']}\n"
    
    if not items:
        text = "📋 Пока нет ни одной вещи."
    
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button())
    await callback.answer()

# ========== ПОИСК ==========
@dp.callback_query(lambda c: c.data == "search_item")
async def search_item_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "🔍 Напиши, что ищем:\n"
        "(Название, размер, цвет или категорию)",
        reply_markup=back_button()
    )
    await state.set_state(SearchForm.query)
    await callback.answer()

@dp.message(SearchForm.query)
async def search_item_result(message: Message, state: FSMContext):
    query = message.text.lower()
    user_id = str(message.from_user.id)
    items = user_data.get(user_id, {}).get("items", [])
    
    found = []
    for item in items:
        if (query in item.get("name", "").lower() or 
            query in item.get("size", "").lower() or 
            query in item.get("color", "").lower() or 
            query in item.get("category", "").lower()):
            found.append(item)
    
    if found:
        for item in found[:5]:
            if item.get("photo"):
                caption = f"🆔 {item['id']} | {item['name']} | {item['size']} | {item['price']} ₽"
                await message.answer_photo(item['photo'], caption=caption)
        await message.answer(
            f"✅ Найдено {len(found)} вещей",
            reply_markup=main_menu()
        )
    else:
        await message.answer(
            "❌ Ничего не найдено. Попробуй другой запрос.",
            reply_markup=main_menu()
        )
    
    await state.clear()

# ========== ПРОДАЖА ==========
@dp.callback_query(lambda c: c.data == "sale")
async def start_sale(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "💰 Напиши <b>ID вещи</b>, которую продала.\n"
        "Посмотреть ID можно в разделе «Мои вещи».",
        parse_mode="HTML",
        reply_markup=back_button()
    )
    await state.set_state(SaleForm.item_id)
    await callback.answer()

@dp.message(SaleForm.item_id)
async def get_sale_price(message: Message, state: FSMContext):
    try:
        item_id = int(message.text)
        user_id = str(message.from_user.id)
        items = user_data.get(user_id, {}).get("items", [])
        
        item = next((i for i in items if i.get("id") == item_id), None)
        if not item:
            await message.answer(
                "❌ Вещь с таким ID не найдена. Попробуй ещё раз.",
                reply_markup=back_button()
            )
            return
        
        await state.update_data(item_id=item_id, item_name=item.get("name"), default_price=item.get("price"))
        await message.answer(
            f"📦 {item.get('name')}\n"
            f"💰 Рекомендуемая цена: {item.get('price')} ₽\n\n"
            f"Напиши <b>цену продажи</b> (число):",
            parse_mode="HTML",
            reply_markup=back_button()
        )
        await state.set_state(SaleForm.price)
    except ValueError:
        await message.answer(
            "❌ Введи число (ID вещи)",
            reply_markup=back_button()
        )

@dp.message(SaleForm.price)
async def save_sale(message: Message, state: FSMContext):
    try:
        price = int(message.text)
        data = await state.get_data()
        item_id = data.get("item_id")
        item_name = data.get("item_name", "Без названия")
        user_id = str(message.from_user.id)
        
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
        
        money = user_data[user_id]["money"]
        money["salary"] += int(price * 0.3)
        money["turnover"] += int(price * 0.4)
        money["post"] += int(price * 0.15)
        money["pillow"] += int(price * 0.1)
        money["dream"] += int(price * 0.05)
        
        await message.answer(
            f"✅ Продажа записана!\n\n"
            f"🆔 Вещь #{item_id}\n"
            f"📦 {item_name} — {price} ₽\n\n"
            f"<b>Деньги разложены:</b>\n"
            f"👩 Себе (30%): {int(price*0.3)} ₽\n"
            f"📦 Оборот (40%): {int(price*0.4)} ₽\n"
            f"📮 Почта (15%): {int(price*0.15)} ₽\n"
            f"🛡️ Подушка (10%): {int(price*0.1)} ₽\n"
            f"✨ Мечта (5%): {int(price*0.05)} ₽",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Ошибка! Введи число",
            reply_markup=back_button()
        )

# ========== СТАТИСТИКА ==========
@dp.callback_query(lambda c: c.data == "stats")
async def show_stats(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
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
    for cat, count in categories.items():
        cat_text += f"{cat}: {count} шт.\n"
    
    stats_text = (
        f"📊 <b>Твоя статистика</b>\n\n"
        f"📦 Продано: {total_sales} шт.\n"
        f"💰 Выручка: {total_revenue} ₽\n"
        f"📈 Средний чек: {avg_price} ₽\n"
        f"📸 Всего вещей: {len(items)} шт.\n\n"
        f"<b>📂 Категории:</b>\n{cat_text or 'Пока нет'}\n"
        f"<b>💰 Конверты:</b>\n"
        f"👩 Себе: {money.get('salary', 0)} ₽\n"
        f"📦 Оборот: {money.get('turnover', 0)} ₽\n"
        f"📮 Почта: {money.get('post', 0)} ₽\n"
        f"🛡️ Подушка: {money.get('pillow', 0)} ₽\n"
        f"✨ Мечта: {money.get('dream', 0)} ₽"
    )
    await callback.message.delete()
    await callback.message.answer(stats_text, parse_mode="HTML", reply_markup=back_button())
    await callback.answer()

# ========== СКРИПТЫ ==========
@dp.callback_query(lambda c: c.data == "scripts")
async def show_scripts(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "🗣 <b>Готовые фразы для общения с покупателями</b>\n\n"
        "1️⃣ <b>Если просят скидку:</b>\n"
        "«Честно, я уже поставила минимум. Но если оформите сегодня — положу в подарок шарфик!»\n\n"
        "2️⃣ <b>Если говорят «Подумаю»:</b>\n"
        "«Понимаю! Такие вещи быстро уходят. Отложу до вечера, потом уйдёт другому.»\n\n"
        "3️⃣ <b>Чтобы привести подругу (сарафанное радио):</b>\n"
        "«Забирайте, и если приведете соседку — скидка 30% на следующую вещь!»\n\n"
        "4️⃣ <b>Закрытие сделки:</b>\n"
        "«Посылка у вас! Если всё понравилось — оставьте отзыв. Заходите ещё!»"
    )
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_button())
    await callback.answer()

# ========== ЗАПУСК ==========
async def main():
    print("✅ Бот с библиотекой промтов запущен!")
    asyncio.create_task(check_reminders())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
