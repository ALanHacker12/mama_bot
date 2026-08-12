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

# ========== ЖЁСТКИЙ ПУТЬ К ФАЙЛУ ==========
DATA_FILE = "/app/data/user_data.json"

# ========== СПИСОК РАЗРЕШЁННЫХ ПОЛЬЗОВАТЕЛЕЙ ==========
ALLOWED_USERS = ["6663434089", "602370918"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_data = load_data()

def ensure_user(user_id):
    if user_id not in ALLOWED_USERS:
        return False
    if "shared" not in user_data:
        user_data["shared"] = {
            "items": [],
            "sales": [],
            "money": {"salary": 0, "turnover": 0, "post": 0, "pillow": 0, "dream": 0},
            "expenses": 0,
            "item_counter": 1
        }
        save_data(user_data)
    if "users" not in user_data:
        user_data["users"] = []
    if user_id not in user_data["users"]:
        user_data["users"].append(user_id)
        save_data(user_data)
    return True

def recalculate_money():
    if "shared" not in user_data:
        return
    sales = user_data["shared"].get("sales", [])
    money = {"salary": 0, "turnover": 0, "post": 0, "pillow": 0, "dream": 0}
    for sale in sales:
        price = sale.get("price", 0)
        money["salary"] += int(price * 0.3)
        money["turnover"] += int(price * 0.4)
        money["post"] += int(price * 0.15)
        money["pillow"] += int(price * 0.1)
        money["dream"] += int(price * 0.05)
    user_data["shared"]["money"] = money

# ========== ПЕРЕВОД КАТЕГОРИЙ (РАСШИРЕННЫЙ) ==========
CATEGORY_TRANSLATE = {
    "Платье": "dress", "Платья": "dress", "Платье": "dress",
    "Пальто": "coat", "Куртка": "jacket", "Куртки": "jacket",
    "Джинсы": "jeans", "Брюки": "pants",
    "Кофта": "sweater", "Кофты": "sweater", "Свитер": "sweater",
    "Рубашка": "shirt", "Блузка": "blouse",
    "Шорты": "shorts", "Юбка": "skirt",
    "Пиджак": "jacket",
    "Боди": "bodysuit",
    "Туника": "tunic",
    "Футболка": "tshirt",
    "Бомбер": "bomber jacket",
    "Тренч": "trench coat",
    "Кардиган": "cardigan",
    "Сарафан": "sundress",
    "Костюм": "suit",
    "Кроп-топ": "crop top",
    "Жилет": "vest",
    "Комбинезон": "jumpsuit"
}

PROMPT_TEMPLATES = {
    "dress": "Professional fashion photography. A beautiful women's {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, folds, fabric texture, and colors exactly as they are. All tags and labels must remain inside the garment, not visible on the front. Soft diffused studio lighting. 8k, hyper-realistic, commercial catalog quality, sharp focus on fabric and details.",
    "coat": "Professional outerwear photography. A stylish {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, draping, fabric texture, and colors. Internal labels must remain hidden inside the garment. Soft diffused lighting. 8k, hyper-realistic, luxury catalog quality.",
    "jacket": "Professional outerwear photography. A stylish {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, draping, fabric texture, and colors. Internal labels must remain hidden inside the garment. Soft diffused lighting. 8k, hyper-realistic, luxury catalog quality.",
    "jeans": "Professional product photography. A pair of {category} perfectly displayed on a minimalist white mannequin. Pure white studio background. Keep the original fit, folds, denim texture, and colors. Tags and labels must stay inside. Soft studio lighting. 8k, sharp focus, commercial quality.",
    "pants": "Professional product photography. A pair of {category} perfectly displayed on a minimalist white mannequin. Pure white studio background. Keep the original fit, folds, fabric texture, and colors. Tags and labels must stay inside. Soft studio lighting. 8k, sharp focus, commercial quality.",
    "sweater": "Professional knitwear photography. A cozy {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the original shape, knit texture, drape, and colors. Labels must remain hidden inside. Soft natural lighting. 8k, hyper-realistic, commercial quality.",
    "blouse": "Professional shirt photography. A crisp {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the original shape, collar, cuffs, fabric texture, and colors. Tags must stay inside. Bright studio lighting. 8k, sharp focus, commercial catalog quality.",
    "shirt": "Professional shirt photography. A crisp {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the original shape, collar, cuffs, fabric texture, and colors. Tags must stay inside. Bright studio lighting. 8k, sharp focus, commercial catalog quality.",
    "shorts": "Professional bottom wear photography. A stylish {category} perfectly displayed on a minimalist white mannequin. Pure white studio background. Keep the original shape, draping, fabric texture, and colors. Labels must remain inside. Soft diffused lighting. 8k, commercial quality.",
    "skirt": "Professional bottom wear photography. A stylish {category} perfectly displayed on a minimalist white mannequin. Pure white studio background. Keep the original shape, draping, fabric texture, and colors. Labels must remain inside. Soft diffused lighting. 8k, commercial quality.",
    "bodysuit": "Professional fashion photography. A beautiful {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, folds, fabric texture, and colors exactly as they are. All tags and labels must remain inside the garment, not visible on the front. Soft diffused studio lighting. 8k, hyper-realistic, commercial catalog quality, sharp focus on fabric and details.",
    "tunic": "Professional fashion photography. A beautiful {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, folds, fabric texture, and colors exactly as they are. All tags and labels must remain inside the garment, not visible on the front. Soft diffused studio lighting. 8k, hyper-realistic, commercial catalog quality, sharp focus on fabric and details.",
    "tshirt": "Professional fashion photography. A beautiful {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, folds, fabric texture, and colors exactly as they are. All tags and labels must remain inside the garment, not visible on the front. Soft diffused studio lighting. 8k, hyper-realistic, commercial catalog quality, sharp focus on fabric and details.",
    "bomber jacket": "Professional outerwear photography. A stylish {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, draping, fabric texture, and colors. Internal labels must remain hidden inside the garment. Soft diffused lighting. 8k, hyper-realistic, luxury catalog quality.",
    "trench coat": "Professional outerwear photography. A stylish {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, draping, fabric texture, and colors. Internal labels must remain hidden inside the garment. Soft diffused lighting. 8k, hyper-realistic, luxury catalog quality.",
    "cardigan": "Professional knitwear photography. A cozy {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the original shape, knit texture, drape, and colors. Labels must remain hidden inside. Soft natural lighting. 8k, hyper-realistic, commercial quality.",
    "sundress": "Professional fashion photography. A beautiful women's {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, folds, fabric texture, and colors exactly as they are. All tags and labels must remain inside the garment, not visible on the front. Soft diffused studio lighting. 8k, hyper-realistic, commercial catalog quality, sharp focus on fabric and details.",
    "suit": "Professional fashion photography. A beautiful women's {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, folds, fabric texture, and colors exactly as they are. All tags and labels must remain inside the garment, not visible on the front. Soft diffused studio lighting. 8k, hyper-realistic, commercial catalog quality, sharp focus on fabric and details.",
    "crop top": "Professional fashion photography. A beautiful {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, folds, fabric texture, and colors exactly as they are. All tags and labels must remain inside the garment, not visible on the front. Soft diffused studio lighting. 8k, hyper-realistic, commercial catalog quality, sharp focus on fabric and details.",
    "vest": "Professional outerwear photography. A stylish {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, draping, fabric texture, and colors. Internal labels must remain hidden inside the garment. Soft diffused lighting. 8k, hyper-realistic, luxury catalog quality.",
    "jumpsuit": "Professional fashion photography. A beautiful {category} perfectly fitted on a minimalist white mannequin torso. Pure white studio background. Keep the exact shape, folds, fabric texture, and colors exactly as they are. All tags and labels must remain inside the garment, not visible on the front. Soft diffused studio lighting. 8k, hyper-realistic, commercial catalog quality, sharp focus on fabric and details.",
    "default": "Professional product photography. The garment perfectly displayed on a minimalist white mannequin. Pure white studio background. Keep the original shape, fabric texture, colors, and all details. All tags and labels must remain hidden inside. Soft studio lighting. 8k, hyper-realistic, commercial catalog quality."
}

def get_prompt_for_category(category, item_name):
    category_en = CATEGORY_TRANSLATE.get(category, "garment")
    template = PROMPT_TEMPLATES.get(category_en, PROMPT_TEMPLATES["default"])
    # Используем английское название категории, а не русское
    return template.format(category=category_en)

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

def item_actions_menu(item_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_item_{item_id}")],
        [InlineKeyboardButton(text="🖼️ Изменить фото", callback_data=f"edit_photo_{item_id}")],
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

# ========== СОСТОЯНИЯ ==========
class ItemForm(StatesGroup):
    photos = State()
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

class EditPhotoForm(StatesGroup):
    item_id = State()
    photos = State()

class SaleForm(StatesGroup):
    item_id = State()
    price = State()

class SearchForm(StatesGroup):
    query = State()

class ExpenseForm(StatesGroup):
    amount = State()

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
            for user_id in ALLOWED_USERS:
                try:
                    await bot.send_message(user_id, random.choice(MORNING_MESSAGES), parse_mode="HTML")
                except:
                    pass
        if current_time == "19:00" and last_evening != now.strftime("%d.%m.%Y"):
            last_evening = now.strftime("%d.%m.%Y")
            for user_id in ALLOWED_USERS:
                try:
                    if "shared" not in user_data:
                        sales_today = 0
                    else:
                        sales_today = len([s for s in user_data["shared"].get("sales", []) if s.get("date") == datetime.now().strftime("%d.%m.%Y")])
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
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа к этому боту.")
        return
    ensure_user(user_id)
    await message.answer(
        "👋 Мама, я твой умный бизнес-секретарь!\n"
        "Я помню каждую вещь, считаю деньги, напоминаю о планах и даю готовые промты для фото на манекене.\n\n"
        "⬇️ Выбери действие:",
        reply_markup=main_menu()
    )

# ========== НАЗАД ==========
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("👋 Главное меню:\n\n⬇️ Выбери действие:", reply_markup=main_menu())
    await callback.answer()

# ========== СТРАТЕГИЯ ==========
@dp.callback_query(lambda c: c.data == "strategy")
async def show_strategy(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    if "shared" not in user_data:
        sales_today = 0
    else:
        sales_today = len([s for s in user_data["shared"].get("sales", []) if s.get("date") == datetime.now().strftime("%d.%m.%Y")])
    text = (f"📅 <b>План на сегодня</b>\n\n✅ Продано сегодня: {sales_today} / 3\n\n📋 <b>Чек-лист:</b>\n1️⃣ Сфотографируй 5 вещей\n2️⃣ Выложи их на Авито в 19:00\n3️⃣ Обнови 10 старых объявлений\n4️⃣ Ответь на все сообщения\n5️⃣ Добавь все продажи в бота\n\n🔥 <b>Совет:</b> Если вещь не продаётся 2 недели — отдай за 199 ₽")
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_menu_button())
    await callback.answer()

# ========== ПРОМТЫ (АВТОМАТИЧЕСКИ ИЗ КАТЕГОРИЙ СТАТИСТИКИ) ==========
@dp.callback_query(lambda c: c.data == "prompt_menu")
async def prompt_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    
    if "shared" not in user_data:
        await callback.message.delete()
        await callback.message.answer("❌ Нет вещей в базе. Добавь сначала вещи.", reply_markup=back_to_menu_button())
        await callback.answer()
        return
    
    items = user_data["shared"].get("items", [])
    categories = {}
    for item in items:
        cat = item.get("category", "Другое")
        categories[cat] = categories.get(cat, 0) + 1
    
    if not categories:
        await callback.message.delete()
        await callback.message.answer("❌ Нет категорий. Добавь сначала вещи.", reply_markup=back_to_menu_button())
        await callback.answer()
        return
    
    kb_buttons = []
    for cat, count in categories.items():
        kb_buttons.append([InlineKeyboardButton(text=f"{cat} ({count})", callback_data=f"prompt_cat_{cat}")])
    kb_buttons.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    
    await callback.message.delete()
    await callback.message.answer(
        "🎨 <b>Выбери категорию вещи</b>\n\n"
        "Я выдам готовый промт для генерации фото на манекене.\n"
        "Просто скопируй его и вставь в Nano Banana / любую нейросеть.\n\n"
        "⬇️ Выбери категорию:",
        parse_mode="HTML",
        reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("prompt_cat_"))
async def prompt_category_selected(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    
    category = callback.data.replace("prompt_cat_", "")
    prompt = get_prompt_for_category(category, category)
    
    # Показываем перевод категории
    category_en = CATEGORY_TRANSLATE.get(category, "garment")
    
    await callback.message.delete()
    await callback.message.answer(
        f"🎨 <b>Промт для категории «{category}»</b>\n"
        f"📌 <b>Перевод:</b> {category_en}\n\n"
        f"<b>⬇️ Скопируй этот текст:</b>\n"
        f"<code>{prompt}</code>\n\n"
        "📌 <b>Инструкция:</b>\n"
        "1️⃣ Скопируй текст выше\n"
        "2️⃣ Вставь в нейросеть (Nano Banana, Midjourney, Kandinsky)\n"
        "3️⃣ Загрузи своё фото вещи\n"
        "4️⃣ Нажми «Сгенерировать»\n\n"
        "✨ Получишь профессиональное фото на манекене!",
        parse_mode="HTML",
        reply_markup=back_to_menu_button()
    )
    await callback.answer()

# ========== ТОП ПРОДАЖ ==========
@dp.callback_query(lambda c: c.data == "top_sales")
async def show_top_sales(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    if "shared" not in user_data:
        text = "🏆 Ты пока ничего не продала. Добавь первую продажу через кнопку «💰 Добавить продажу»"
    else:
        sales = user_data["shared"].get("sales", [])
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
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer(
        "📸 <b>Добавляем новую вещь</b>\n\n"
        "Отправь мне <b>фото</b> вещи (до 5 фото).\n"
        "Можно отправить несколько фото за раз.\n"
        "Когда закончишь — напиши «готово».",
        parse_mode="HTML",
        reply_markup=back_to_menu_button()
    )
    await state.update_data(photos=[])
    await state.set_state(ItemForm.photos)
    await callback.answer()

@dp.message(ItemForm.photos, F.photo)
async def item_photo(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
    ensure_user(user_id)
    data = await state.get_data()
    photos = data.get("photos", [])
    photo_id = message.photo[-1].file_id
    photos.append(photo_id)
    await state.update_data(photos=photos)
    if len(photos) >= 5:
        await message.answer("✅ Получено 5 фото. Теперь напиши <b>название</b> вещи:", parse_mode="HTML", reply_markup=back_button("add_item_menu"))
        await state.set_state(ItemForm.name)
    else:
        await message.answer(f"📸 Фото сохранено ({len(photos)}/5). Отправь ещё или напиши «готово», если закончила.", reply_markup=back_button("add_item_menu"))

@dp.message(ItemForm.photos)
async def item_photos_done(message: Message, state: FSMContext):
    if message.text.lower() == "готово":
        data = await state.get_data()
        photos = data.get("photos", [])
        if not photos:
            await message.answer("❌ Ты не отправила ни одного фото. Отправь хотя бы одно фото.", reply_markup=back_button("add_item_menu"))
            return
        await message.answer("📝 Теперь напиши <b>название</b> вещи:", parse_mode="HTML", reply_markup=back_button("add_item_menu"))
        await state.set_state(ItemForm.name)
    else:
        await message.answer("📸 Отправь фото или напиши «готово», если закончила.", reply_markup=back_button("add_item_menu"))

@dp.message(ItemForm.name)
async def item_name(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
    ensure_user(user_id)
    name = message.text.strip()
    if not name:
        await message.answer("❌ Название не может быть пустым. Напиши название вещи:", reply_markup=back_button("add_item_menu"))
        return
    await state.update_data(name=name)
    await message.answer(
        "📏 Напиши <b>размер</b> (46, M, L):",
        parse_mode="HTML",
        reply_markup=back_button("item_back_to_name")
    )
    await state.set_state(ItemForm.size)

@dp.message(ItemForm.size)
async def item_size(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
    ensure_user(user_id)
    await state.update_data(size=message.text.strip())
    await message.answer(
        "🎨 Напиши <b>цвет</b>:",
        parse_mode="HTML",
        reply_markup=back_button("item_back_to_size")
    )
    await state.set_state(ItemForm.color)

@dp.message(ItemForm.color)
async def item_color(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
    ensure_user(user_id)
    await state.update_data(color=message.text.strip())
    await message.answer(
        "🏷️ Напиши <b>категорию</b> (любую, например: Платья, Кофты, Боди, Пиджак):",
        parse_mode="HTML",
        reply_markup=back_button("item_back_to_color")
    )
    await state.set_state(ItemForm.category)

@dp.message(ItemForm.category)
async def item_category(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
    ensure_user(user_id)
    await state.update_data(category=message.text.strip())
    await message.answer(
        "🏷️ Напиши <b>теги</b> (например: летнее, офис, праздник).\nМожно перечислить через запятую. Если не хочешь — напиши «нет».",
        parse_mode="HTML",
        reply_markup=back_button("item_back_to_category")
    )
    await state.set_state(ItemForm.tags)

@dp.message(ItemForm.tags)
async def item_tags(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
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
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
    ensure_user(user_id)
    try:
        price = int(message.text.strip())
        data = await state.get_data()
        
        item_id = user_data["shared"]["item_counter"]
        user_data["shared"]["item_counter"] += 1
        user_data["shared"]["items"].append({
            "id": item_id,
            "name": data.get("name"),
            "size": data.get("size"),
            "color": data.get("color"),
            "category": data.get("category"),
            "tags": data.get("tags", ""),
            "price": price,
            "photos": data.get("photos", []),
            "status": "active",
            "created": datetime.now().strftime("%d.%m.%Y")
        })
        save_data(user_data)
        
        for photo_id in data.get("photos", [])[:5]:
            await message.answer_photo(photo_id)
        
        await message.answer(
            f"✅ <b>Вещь добавлена!</b>\n\n"
            f"🆔 <b>ID:</b> {item_id}\n"
            f"📦 {data.get('name')}\n"
            f"📏 Размер: {data.get('size')}\n"
            f"🎨 Цвет: {data.get('color')}\n"
            f"🏷️ Категория: {data.get('category')}\n"
            f"🏷️ Теги: {data.get('tags') or 'нет'}\n"
            f"💰 Цена: {price} ₽\n"
            f"📸 Фото: {len(data.get('photos', []))} шт.",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer(
            "❌ Ошибка! Введи число, например: 1200",
            reply_markup=back_button("item_back_to_price")
        )

# ========== ОБРАБОТЧИКИ ВОЗВРАТА ==========
@dp.callback_query(lambda c: c.data == "item_back_to_name")
async def back_to_name(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("📝 Напиши <b>название</b> вещи:", parse_mode="HTML", reply_markup=back_button("add_item_menu"))
    await state.set_state(ItemForm.name)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_size")
async def back_to_size(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("📏 Напиши <b>размер</b> (46, M, L):", parse_mode="HTML", reply_markup=back_button("item_back_to_name"))
    await state.set_state(ItemForm.size)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_color")
async def back_to_color(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("🎨 Напиши <b>цвет</b>:", parse_mode="HTML", reply_markup=back_button("item_back_to_size"))
    await state.set_state(ItemForm.color)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_category")
async def back_to_category(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("🏷️ Напиши <b>категорию</b> (любую, например: Платья, Кофты, Боди, Пиджак):", parse_mode="HTML", reply_markup=back_button("item_back_to_color"))
    await state.set_state(ItemForm.category)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_tags")
async def back_to_tags(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("🏷️ Напиши <b>теги</b> (например: летнее, офис, праздник).\nМожно перечислить через запятую. Если не хочешь — напиши «нет».", parse_mode="HTML", reply_markup=back_button("item_back_to_category"))
    await state.set_state(ItemForm.tags)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "item_back_to_price")
async def back_to_price(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
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
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    items = user_data["shared"].get("items", [])
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
        f"📸 Фото: {len(item.get('photos', []))} шт.\n"
        f"📌 Статус: {item.get('status', 'активна')}\n\n"
        "⬇️ Выбери, что хочешь изменить:",
        parse_mode="HTML",
        reply_markup=edit_item_menu(item_id)
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("edit_name_"))
async def edit_name_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
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
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
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
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
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
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    await state.update_data(item_id=item_id, field="category")
    await callback.message.delete()
    await callback.message.answer("🏷️ Напиши <b>новую категорию</b> (любую):", parse_mode="HTML", reply_markup=back_button(f"edit_item_{item_id}"))
    await state.set_state(EditForm.value)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("edit_tags_"))
async def edit_tags_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
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
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
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
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
    ensure_user(user_id)
    data = await state.get_data()
    item_id = data.get("item_id")
    field = data.get("field")
    new_value = message.text.strip()
    items = user_data["shared"].get("items", [])
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

# ========== РЕДАКТИРОВАНИЕ ФОТО ==========
@dp.callback_query(lambda c: c.data.startswith("edit_photo_"))
async def edit_photo_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    await state.update_data(item_id=item_id, photos=[])
    await callback.message.delete()
    await callback.message.answer(
        "🖼️ <b>Изменить фото</b>\n\n"
        "Отправь мне <b>новые фото</b> (до 5 фото).\n"
        "Когда закончишь — напиши «готово».",
        parse_mode="HTML",
        reply_markup=back_button(f"edit_item_{item_id}")
    )
    await state.set_state(EditPhotoForm.photos)
    await callback.answer()

@dp.message(EditPhotoForm.photos, F.photo)
async def edit_photo_receive(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
    ensure_user(user_id)
    data = await state.get_data()
    photos = data.get("photos", [])
    photo_id = message.photo[-1].file_id
    photos.append(photo_id)
    await state.update_data(photos=photos)
    if len(photos) >= 5:
        await message.answer("✅ Получено 5 фото. Сохраняю...")
        await save_new_photos(message, state)
    else:
        await message.answer(f"📸 Фото сохранено ({len(photos)}/5). Отправь ещё или напиши «готово».", reply_markup=back_button(f"edit_item_{data.get('item_id')}"))

@dp.message(EditPhotoForm.photos)
async def edit_photo_done(message: Message, state: FSMContext):
    if message.text.lower() == "готово":
        await save_new_photos(message, state)
    else:
        await message.answer("📸 Отправь фото или напиши «готово», если закончила.", reply_markup=back_button(f"edit_item_{data.get('item_id')}"))

async def save_new_photos(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    ensure_user(user_id)
    data = await state.get_data()
    item_id = data.get("item_id")
    photos = data.get("photos", [])
    if not photos:
        await message.answer("❌ Ты не отправила ни одного фото. Изменения отменены.", reply_markup=main_menu())
        await state.clear()
        return
    items = user_data["shared"].get("items", [])
    item = next((i for i in items if i.get("id") == item_id), None)
    if not item:
        await message.answer("❌ Вещь не найдена.", reply_markup=main_menu())
        await state.clear()
        return
    item["photos"] = photos
    save_data(user_data)
    await message.answer(
        f"✅ <b>Фото обновлены!</b>\n\n"
        f"🆔 ID: {item_id}\n"
        f"📦 {item['name']}\n"
        f"📸 Фото: {len(photos)} шт.",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    await state.clear()

@dp.callback_query(lambda c: c.data == "back_to_items")
async def back_to_items(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    await callback.message.delete()
    await show_items(callback, state)

# ========== УДАЛЕНИЕ ВЕЩИ ==========
@dp.callback_query(lambda c: c.data.startswith("delete_item_"))
async def delete_item_confirm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    items = user_data["shared"].get("items", [])
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
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    item_id = int(callback.data.split("_")[2])
    items = user_data["shared"].get("items", [])
    item = next((i for i in items if i.get("id") == item_id), None)
    if not item:
        await callback.message.delete()
        await callback.message.answer("❌ Вещь не найдена.", reply_markup=back_to_menu_button())
        await callback.answer()
        return
    user_data["shared"]["items"] = [i for i in items if i.get("id") != item_id]
    sales = user_data["shared"].get("sales", [])
    user_data["shared"]["sales"] = [s for s in sales if s.get("item_id") != item_id]
    recalculate_money()
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
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("❌ Удаление отменено.", reply_markup=main_menu())
    await callback.answer()

# ========== МОИ ВЕЩИ ==========
@dp.callback_query(lambda c: c.data == "items")
async def show_items(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    if "shared" not in user_data:
        items = []
    else:
        items = user_data["shared"].get("items", [])
    
    if not items:
        await callback.message.delete()
        await callback.message.answer("📸 У тебя пока нет вещей в базе.\n\nДобавь первую вещь через кнопку «➕ Добавить вещь»", reply_markup=back_to_menu_button())
        await callback.answer()
        return
    
    total = len(items)
    active = len([i for i in items if i.get("status") == "active"])
    
    await callback.message.delete()
    await callback.message.answer(
        f"📸 <b>Все вещи ({total} шт.)</b>\n"
        f"✅ Активных: {active} | ❌ Продано: {total - active}\n\n"
        f"⬇️ Показываю все вещи:",
        parse_mode="HTML"
    )
    
    for item in items:
        if item.get("photos"):
            status_emoji = "✅" if item.get("status") == "active" else "❌"
            caption = (f"{status_emoji} <b>ID:</b> {item['id']}\n"
                       f"📦 {item['name']}\n"
                       f"📏 Размер: {item['size']}\n"
                       f"🎨 Цвет: {item['color']}\n"
                       f"🏷️ {item['category']}\n"
                       f"🏷️ Теги: {item.get('tags', 'нет')}\n"
                       f"💰 {item['price']} ₽\n"
                       f"📅 {item.get('created', '')}")
            photos = item.get("photos", [])
            if photos:
                await callback.message.answer_photo(
                    photos[0],
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=item_actions_menu(item['id'])
                )
                for photo_id in photos[1:]:
                    await callback.message.answer_photo(photo_id)
        elif item.get("photo"):
            status_emoji = "✅" if item.get("status") == "active" else "❌"
            caption = (f"{status_emoji} <b>ID:</b> {item['id']}\n"
                       f"📦 {item['name']}\n"
                       f"📏 Размер: {item['size']}\n"
                       f"🎨 Цвет: {item['color']}\n"
                       f"🏷️ {item['category']}\n"
                       f"🏷️ Теги: {item.get('tags', 'нет')}\n"
                       f"💰 {item['price']} ₽\n"
                       f"📅 {item.get('created', '')}")
            await callback.message.answer_photo(
                item['photo'],
                caption=caption,
                parse_mode="HTML",
                reply_markup=item_actions_menu(item['id'])
            )
    
    await show_items_list(callback, state)

# ========== СПИСОК ВСЕХ ВЕЩЕЙ С ГАЛОЧКАМИ ==========
@dp.callback_query(lambda c: c.data == "items_list")
async def show_items_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    if "shared" not in user_data:
        items = []
    else:
        items = user_data["shared"].get("items", [])
    
    if not items:
        text = "📋 Пока нет ни одной вещи."
    else:
        active = [i for i in items if i.get("status") == "active"]
        sold = [i for i in items if i.get("status") == "sold"]
        text = f"📋 <b>Список всех вещей</b>\n\n✅ Активных: {len(active)}\n❌ Продано: {len(sold)}\n\n"
        for item in items:
            status = "✅" if item.get("status") == "active" else "❌"
            text += f"{status} 🆔{item['id']} | {item['name']} | {item['size']} | {item.get('category', '')}\n"
    
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=back_to_menu_button()
    )
    await callback.answer()

# ========== ПОИСК ==========
@dp.callback_query(lambda c: c.data == "search_item")
async def search_item_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer(
        "🔍 Напиши, что ищем:\n"
        "(Название, размер, цвет, категорию, тег или ID)",
        reply_markup=back_to_menu_button()
    )
    await state.set_state(SearchForm.query)
    await callback.answer()

@dp.message(SearchForm.query)
async def search_item_result(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
    ensure_user(user_id)
    query = message.text.lower().strip()
    if "shared" not in user_data:
        items = []
    else:
        items = user_data["shared"].get("items", [])
    
    found = []
    
    # Если запрос — число, ищем ТОЛЬКО по ID (точное совпадение)
    if query.isdigit():
        for item in items:
            if item.get("id") == int(query):
                found.append(item)
                break
    else:
        # Текстовый поиск
        for item in items:
            if (query in str(item.get("id")).lower() or
                query in item.get("name", "").lower() or 
                query in item.get("size", "").lower() or 
                query in item.get("color", "").lower() or 
                query in item.get("category", "").lower() or 
                query in item.get("tags", "").lower()):
                found.append(item)
    
    if not found:
        await message.answer("❌ Ничего не найдено. Попробуй другой запрос.", reply_markup=main_menu())
        await state.clear()
        return
    
    await message.answer(f"🔍 Найдено {len(found)} вещей:")
    
    for item in found:
        status_emoji = "✅" if item.get("status") == "active" else "❌"
        if item.get("photos"):
            caption = (f"{status_emoji} <b>ID:</b> {item['id']}\n"
                       f"📦 {item['name']}\n"
                       f"📏 Размер: {item['size']}\n"
                       f"🎨 Цвет: {item['color']}\n"
                       f"🏷️ {item['category']}\n"
                       f"💰 {item['price']} ₽\n"
                       f"📌 Статус: {'✅ Активна' if item.get('status') == 'active' else '❌ Продана'}")
            photos = item.get("photos", [])
            if photos:
                await message.answer_photo(
                    photos[0],
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=item_actions_menu(item['id'])
                )
                for photo_id in photos[1:]:
                    await message.answer_photo(photo_id)
        elif item.get("photo"):
            caption = (f"{status_emoji} <b>ID:</b> {item['id']}\n"
                       f"📦 {item['name']}\n"
                       f"📏 Размер: {item['size']}\n"
                       f"🎨 Цвет: {item['color']}\n"
                       f"🏷️ {item['category']}\n"
                       f"💰 {item['price']} ₽\n"
                       f"📌 Статус: {'✅ Активна' if item.get('status') == 'active' else '❌ Продана'}")
            await message.answer_photo(
                item['photo'],
                caption=caption,
                parse_mode="HTML",
                reply_markup=item_actions_menu(item['id'])
            )
    
    await message.answer(f"✅ Показано {len(found)} вещей.", reply_markup=main_menu())
    await state.clear()

# ========== ПРОДАЖА ==========
@dp.callback_query(lambda c: c.data == "sale")
async def start_sale(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer("💰 Напиши <b>ID вещи</b>, которую продала.\nПосмотреть ID можно в разделе «Мои вещи».", parse_mode="HTML", reply_markup=back_to_menu_button())
    await state.set_state(SaleForm.item_id)
    await callback.answer()

@dp.message(SaleForm.item_id)
async def get_sale_price(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
    ensure_user(user_id)
    try:
        item_id = int(message.text.strip())
        if "shared" not in user_data:
            items = []
        else:
            items = user_data["shared"].get("items", [])
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
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
    ensure_user(user_id)
    try:
        price = int(message.text.strip())
        data = await state.get_data()
        item_id = data.get("item_id")
        item_name = data.get("item_name", "Без названия")
        
        user_data["shared"]["sales"].append({
            "item_id": item_id,
            "name": item_name,
            "price": price,
            "date": datetime.now().strftime("%d.%m.%Y")
        })
        for item in user_data["shared"]["items"]:
            if item.get("id") == item_id:
                item["status"] = "sold"
                break
        recalculate_money()
        save_data(user_data)
        
        await message.answer(
            f"✅ Продажа записана!\n\n🆔 Вещь #{item_id}\n📦 {item_name} — {price} ₽\n\n<b>Деньги разложены:</b>\n👩 Себе (30%): {int(price*0.3)} ₽\n📦 Оборот (40%): {int(price*0.4)} ₽\n📮 Почта (15%): {int(price*0.15)} ₽\n🛡️ Подушка (10%): {int(price*0.1)} ₽\n✨ Мечта (5%): {int(price*0.05)} ₽",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Ошибка! Введи число", reply_markup=back_to_menu_button())

# ========== СТАТИСТИКА ==========
@dp.callback_query(lambda c: c.data == "stats")
async def show_stats(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    if "shared" not in user_data:
        sales = []
        items = []
        expenses = 0
        money = {"salary": 0, "turnover": 0, "post": 0, "pillow": 0, "dream": 0}
    else:
        sales = user_data["shared"].get("sales", [])
        items = user_data["shared"].get("items", [])
        expenses = user_data["shared"].get("expenses", 0)
        money = user_data["shared"].get("money", {"salary": 0, "turnover": 0, "post": 0, "pillow": 0, "dream": 0})
    
    total_sales = len(sales)
    total_revenue = sum(s.get("price", 0) for s in sales)
    avg_price = int(total_revenue / total_sales) if total_sales > 0 else 0
    total_items_sum = sum(item.get("price", 0) for item in items)
    net_profit = total_revenue - expenses
    
    categories = {}
    for item in items:
        cat = item.get("category", "Другое")
        categories[cat] = categories.get(cat, 0) + 1
    
    cat_text = ""
    for cat, count in categories.items():
        cat_text += f"{cat}: {count} шт.\n"
    if not cat_text:
        cat_text = "Пока нет категорий"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Добавить расходы на партию", callback_data="add_expense")],
        [InlineKeyboardButton(text="↩️ Отменить последнюю продажу", callback_data="undo_last_sale")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")]
    ])
    
    stats_text = (f"📊 <b>Твоя статистика</b>\n\n"
                  f"📦 Продано: {total_sales} шт.\n"
                  f"💰 Выручка: {total_revenue} ₽\n"
                  f"📈 Средний чек: {avg_price} ₽\n"
                  f"📸 Всего вещей: {len(items)} шт.\n"
                  f"💎 Общая сумма всех вещей: {total_items_sum} ₽\n"
                  f"📦 Расходы на партию: {expenses} ₽\n"
                  f"📈 Чистая прибыль: {net_profit} ₽\n\n"
                  f"<b>📂 Категории:</b>\n{cat_text}\n"
                  f"<b>💰 Конверты:</b>\n"
                  f"👩 Себе: {money.get('salary', 0)} ₽\n"
                  f"📦 Оборот: {money.get('turnover', 0)} ₽\n"
                  f"📮 Почта: {money.get('post', 0)} ₽\n"
                  f"🛡️ Подушка: {money.get('pillow', 0)} ₽\n"
                  f"✨ Мечта: {money.get('dream', 0)} ₽")
    await callback.message.delete()
    await callback.message.answer(stats_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

# ========== ДОБАВЛЕНИЕ РАСХОДОВ ==========
@dp.callback_query(lambda c: c.data == "add_expense")
async def add_expense_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    await callback.message.delete()
    await callback.message.answer(
        "💰 <b>Добавить расходы на новую партию</b>\n\n"
        "Напиши сумму, которую ты потратила на закупку новых вещей (число):",
        parse_mode="HTML",
        reply_markup=back_to_menu_button()
    )
    await state.set_state(ExpenseForm.amount)
    await callback.answer()

@dp.message(ExpenseForm.amount)
async def save_expense(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    if user_id not in ALLOWED_USERS:
        await message.answer("❌ У тебя нет доступа.")
        await state.clear()
        return
    ensure_user(user_id)
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0. Попробуй ещё раз.", reply_markup=back_to_menu_button())
            return
        if "shared" not in user_data:
            user_data["shared"] = {"expenses": 0}
        user_data["shared"]["expenses"] = user_data["shared"].get("expenses", 0) + amount
        save_data(user_data)
        await message.answer(
            f"✅ <b>Расходы добавлены!</b>\n\n"
            f"💰 Сумма: {amount} ₽\n"
            f"📦 Всего расходов: {user_data['shared']['expenses']} ₽",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer("❌ Ошибка! Введи число, например: 5000", reply_markup=back_to_menu_button())

# ========== ОТМЕНА ПОСЛЕДНЕЙ ПРОДАЖИ ==========
@dp.callback_query(lambda c: c.data == "undo_last_sale")
async def undo_last_sale(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = str(callback.from_user.id)
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    if "shared" not in user_data:
        await callback.message.delete()
        await callback.message.answer("❌ Нет продаж, которые можно отменить.", reply_markup=back_to_menu_button())
        await callback.answer()
        return
    sales = user_data["shared"].get("sales", [])
    if not sales:
        await callback.message.delete()
        await callback.message.answer("❌ Нет продаж, которые можно отменить.", reply_markup=back_to_menu_button())
        await callback.answer()
        return
    last_sale = sales[-1]
    item_id = last_sale.get("item_id")
    item_name = last_sale.get("name", "Без названия")
    price = last_sale.get("price", 0)
    user_data["shared"]["sales"] = sales[:-1]
    for item in user_data["shared"]["items"]:
        if item.get("id") == item_id:
            item["status"] = "active"
            break
    recalculate_money()
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
    if user_id not in ALLOWED_USERS:
        await callback.message.delete()
        await callback.message.answer("❌ У тебя нет доступа.")
        await callback.answer()
        return
    ensure_user(user_id)
    text = ("🗣 <b>Готовые фразы для общения с покупателями</b>\n\n1️⃣ <b>Если просят скидку:</b>\n«Честно, я уже поставила минимум. Но если оформите сегодня — положу в подарок шарфик!»\n\n2️⃣ <b>Если говорят «Подумаю»:</b>\n«Понимаю! Такие вещи быстро уходят. Отложу до вечера, потом уйдёт другому.»\n\n3️⃣ <b>Чтобы привести подругу:</b>\n«Забирайте, и если приведете соседку — скидка 30% на следующую вещь!»\n\n4️⃣ <b>Закрытие сделки:</b>\n«Посылка у вас! Если всё понравилось — оставьте отзыв. Заходите ещё!»")
    await callback.message.delete()
    await callback.message.answer(text, parse_mode="HTML", reply_markup=back_to_menu_button())
    await callback.answer()

# ========== ЗАПУСК ==========
async def main():
    print("✅ Бот с обновлённым поиском, всеми вещами, 5 фото, отчётом, автоматическими промтами из категорий и переводом на английский запущен!")
    asyncio.create_task(check_reminders())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
