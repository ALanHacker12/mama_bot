import asyncio
import logging
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aioschedule

# ========== ТОКЕН ==========
TOKEN = "СЮДА_ВАШ_ТОКЕН"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

# ========== БАЗА ШАБЛОНОВ ПРОМТОВ (ПО КАТЕГОРИЯМ) ==========
PROMPT_TEMPLATES = {
    "dress": "Professional e-commerce product photo of a {description} displayed on a minimalist wooden hanger. Clean white studio background, soft diffused lighting from the left, no harsh shadows. The fabric texture is highly detailed, realistic 8k resolution, commercial photography style, bright and airy, no wrinkles, pure white backdrop, perfect for online store catalog. Show the full front view, side drape, and close-up of the collar based on the provided angles.",
    
    "coat": "High-end fashion studio photography of a {description} elegantly displayed on a sleek mannequin torso. Premium winter/autumn outerwear. The background is pure white (RGB 255). Soft box lighting, highlighting the flow of the fabric and the depth of the color. 8k, hyper-realistic, sharp focus on the textile weave, minimalistic, premium look, no visible tags or logos.",
    
    "pants": "Professional product photography of {description} laid flat on a clean white surface. Studio lighting, sharp focus on the denim texture and stitching details. Crisp, high-contrast image, commercial catalog style, 8k resolution, pure white background, perfect for online store. Show front view, back view with pockets, and belt loops.",
    
    "sweater": "Cozy knitwear studio shot of a {description} on a wooden hanger. Soft natural lighting, white background, detailed texture of the knit fabric, realistic colors, commercial fashion photography, bright and warm atmosphere, 8k resolution, sharp focus on the collar and cuffs.",
    
    "shirt": "Crisp professional product photo of a {description} laid flat on a white background. Studio lighting, perfect ironed look, sharp focus on the collar, cuffs, and button placket. Minimalist, high-end catalog style, 8k resolution, pure white backdrop, commercial quality.",
    
    "short": "Modern e-commerce photo of {description} on a minimalist hanger. Clean white studio background, soft diffused lighting, detailed fabric texture, realistic colors, bright and airy look, 8k resolution, perfect for online store catalog. Show front and back views.",
    
    "default": "Professional product photography of a {description} on a clean white background. Studio lighting, sharp focus on the fabric texture and details, realistic colors, 8k resolution, commercial quality, minimalist style, perfect for online catalog."
}

# ========== РАЗНЫЕ ФОРМУЛИРОВКИ НАПОМИНАНИЙ ==========
MORNING_MESSAGES = [
    "🌅 Доброе утро! Сегодня отличный день для продаж! 📸 Сфоткай 5 вещей и выложи на Авито.",
    "🌞 Вставай, мама! Новая партия ждёт своего покупателя. Сегодня цель — 3 продажи! 💪",
    "☀️ Утро начинается с плана: 5 фото, 5 объявлений, 5 ответов покупателям. Ты справишься! 🚀",
    "🌅 Солнце уже высоко, а твои вещи всё ещё ждут новых хозяев. Действуй! 👗",
    "✨ Доброе утро! Помни: каждый день — это новый шанс продать всё, что лежит на вешалках!",
    "📸 Просыпайся, мама! Сегодня нужно сделать 5 крутых фото и покорить Авито! 🔥"
]

EVENING_MESSAGES = [
    "🌙 Отличная работа сегодня! Проверь сообщения и обнови объявления. Завтра будет новый день! 🌟",
    "🌙 День закончен. Посчитай продажи и запиши их в бота. Отдыхай, ты заслужила! 💤",
    "🌙 Время подводить итоги! Сколько вещей продала сегодня? Не забудь обновить объявления! 📊",
    "🌙 Ты молодец! Даже если продаж мало — главное, ты двигаешься вперёд. Завтра будет лучше! 💪",
    "🌙 Вечерний чек-лист: ответь на все сообщения, обнови объявления, отдохни! 🌟",
    "🌙 Устала? Проверь Авито, ответь покупателям и ложись спать. Завтра новые свершения! 🚀"
]

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
        [InlineKeyboardButton(text="🎨 Промт для фото", callback_data="prompt_menu")]
    ])
    return kb

def back_button():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])
    return kb

# ========== СОСТОЯНИЯ ==========
class PromptForm(StatesGroup):
    description = State()

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

# ========== ФУНКЦИЯ ОПРЕДЕЛЕНИЯ КАТЕГОРИИ ==========
def detect_category(text):
    text_lower = text.lower()
    keywords = {
        "dress": ["плать", "сарафан", "туника"],
        "coat": ["пальт", "куртк", "пухов", "шуба", "дубленк"],
        "pants": ["джинс", "брюк", "штаны", "леггинс"],
        "sweater": ["кофт", "свитер", "джемпер", "пуловер", "кардиган"],
        "shirt": ["рубашк", "блузк", "сорочк"],
        "short": ["шорт", "юбк", "бермуд"]
    }
    
    for category, words in keywords.items():
        for word in words:
            if word in text_lower:
                return category
    return "default"

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
        "Я помню каждую вещь, считаю деньги, напоминаю о планах и помогаю создавать крутые фото.\n\n"
        "⬇️ Выбери действие:",
        reply_markup=main_menu()
    )

# ========== НАЗАД ==========
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👋 Главное меню:\n\n⬇️ Выбери действие:",
        reply_markup=main_menu()
    )
    await callback.answer()

# ========== ЕЖЕДНЕВНЫЕ НАПОМИНАНИЯ (СЛУЧАЙНЫЕ) ==========
async def morning_reminder():
    for user_id in user_data.keys():
        try:
            msg = random.choice(MORNING_MESSAGES)
            await bot.send_message(user_id, msg, parse_mode="HTML")
        except:
            pass

async def evening_reminder():
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

async def scheduler():
    aioschedule.every().day.at("09:00").do(morning_reminder)
    aioschedule.every().day.at("19:00").do(evening_reminder)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(60)

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
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button())
    await callback.answer()

# ========== МЕНЮ ПРОМТОВ (НОВОЕ) ==========
@dp.callback_query(lambda c: c.data == "prompt_menu")
async def prompt_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎨 <b>Генератор промтов для Nano Banana</b>\n\n"
        "Напиши <b>название вещи</b> на русском.\n"
        "Я сам определю категорию и сгенерирую идеальный промт!\n\n"
        "📝 <b>Примеры:</b>\n"
        "• <i>летнее платье с цветочным принтом</i>\n"
        "• <i>зимнее пальто с поясом, двубортное</i>\n"
        "• <i>джинсы скинни тёмно-синие</i>\n\n"
        "Можешь добавить любые детали — я учту всё!",
        parse_mode="HTML",
        reply_markup=back_button()
    )
    await state.set_state(PromptForm.description)
    await callback.answer()

@dp.message(PromptForm.description)
async def generate_prompt(message: Message, state: FSMContext):
    description = message.text.strip()
    
    if len(description) < 3:
        await message.answer(
            "❌ Слишком короткое описание. Напиши подробнее, что это за вещь.",
            reply_markup=back_button()
        )
        return
    
    # Определяем категорию
    category = detect_category(description)
    template = PROMPT_TEMPLATES.get(category, PROMPT_TEMPLATES["default"])
    
    # Генерируем промт
    prompt = template.format(description=description)
    
    # Показываем категорию и промт
    category_names = {
        "dress": "👗 Платье",
        "coat": "🧥 Пальто/Куртка",
        "pants": "👖 Джинсы/Брюки",
        "sweater": "👚 Кофта/Свитер",
        "shirt": "👕 Рубашка/Блузка",
        "short": "🩳 Шорты/Юбка",
        "default": "👔 Другое"
    }
    
    full_response = (
        f"🎨 <b>Твой промт для Nano Banana</b>\n\n"
        f"📌 <b>Категория:</b> {category_names.get(category, 'Другое')}\n"
        f"📝 <b>Описание:</b> {description}\n\n"
        f"<b>⬇️ Скопируй этот текст:</b>\n"
        f"<code>{prompt}</code>\n\n"
        "📌 <b>Инструкция:</b>\n"
        "1️⃣ Скопируй текст выше\n"
        "2️⃣ Вставь в Nano Banana\n"
        "3️⃣ Загрузи 5-6 фото с разных ракурсов\n"
        "4️⃣ Нажми «Сгенерировать»\n\n"
        "✨ Готово! Фото будет как в бутике!"
    )
    
    await message.answer(full_response, parse_mode="HTML", reply_markup=main_menu())
    await state.clear()

# ========== ДОБАВЛЕНИЕ ВЕЩИ С ФОТО ==========
@dp.callback_query(lambda c: c.data == "add_item_menu")
async def add_item_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "📸 <b>Добавляем новую вещь</b>\n\n"
        "Отправь мне <b>фото</b> вещи (одно фото).\n"
        "После этого я спрошу название, размер, цвет и цену.",
        parse_mode="HTML",
        reply_markup=back_button()
    )
    await state.set_state(ItemForm.photo)
    await callback.answer()

@dp.message(ItemForm.photo, F.photo)
async def get_item_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await message.answer(
        "📝 Напиши <b>название</b> вещи (например: Платье летнее):",
        parse_mode="HTML",
        reply_markup=back_button()
    )
    await state.set_state(ItemForm.name)

@dp.message(ItemForm.name)
async def get_item_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "📏 Напиши <b>размер</b> (46, M, L):",
        parse_mode="HTML",
        reply_markup=back_button()
    )
    await state.set_state(ItemForm.size)

@dp.message(ItemForm.size)
async def get_item_size(message: Message, state: FSMContext):
    await state.update_data(size=message.text)
    await message.answer(
        "🎨 Напиши <b>цвет</b>:",
        parse_mode="HTML",
        reply_markup=back_button()
    )
    await state.set_state(ItemForm.color)

@dp.message(ItemForm.color)
async def get_item_color(message: Message, state: FSMContext):
    await state.update_data(color=message.text)
    await message.answer(
        "🏷️ Напиши <b>категорию</b> (Платья, Кофты, Джинсы, Шорты, Куртки):",
        parse_mode="HTML",
        reply_markup=back_button()
    )
    await state.set_state(ItemForm.category)

@dp.message(ItemForm.category)
async def get_item_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer(
        "💰 Напиши <b>цену</b> (число):",
        parse_mode="HTML",
        reply_markup=back_button()
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
                f"💰 Цена: {price} ₽\n"
                f"📅 Добавлена: {datetime.now().strftime('%d.%m.%Y')}"
            ),
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Ошибка! Введи число, например: 1200",
            reply_markup=back_button()
        )

# ========== МОИ ВЕЩИ ==========
@dp.callback_query(lambda c: c.data == "items")
async def show_items(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    items = user_data.get(user_id, {}).get("items", [])
    
    if not items:
        text = "📸 У тебя пока нет вещей в базе.\n\nДобавь первую вещь через кнопку «➕ Добавить вещь»"
        await callback.message.edit_text(text, reply_markup=back_button())
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
    await callback.message.edit_text(
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
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button())
    await callback.answer()

# ========== ПОИСК ==========
@dp.callback_query(lambda c: c.data == "search_item")
async def search_item_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
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
    await callback.message.edit_text(
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
    await callback.message.edit_text(stats_text, parse_mode="HTML", reply_markup=back_button())
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
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_button())
    await callback.answer()

# ========== ЗАПУСК ==========
async def main():
    print("✅ Бот с умными промтами запущен!")
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
