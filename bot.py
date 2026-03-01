import asyncio
import logging
import json
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime, timedelta
import pytz

# ==================== ТВОИ ДАННЫЕ ====================
BOT_TOKEN = "8640012758:AAFhVeVAleSvtg36-dFbaYxUY5Zl8o-9_ck"
OWNER_ID = 7470989833
OWNER_LEVEL = 1000

# ==================== НАСТРОЙКА ЧАСОВОГО ПОЯСА ====================
MSK_TZ = pytz.timezone('Europe/Moscow')

def get_msk_time():
    """Возвращает текущее время в МСК"""
    return datetime.now(MSK_TZ)

def get_msk_date():
    """Возвращает текущую дату в МСК"""
    return get_msk_time().strftime("%Y-%m-%d")

def get_msk_weekday():
    """Возвращает номер дня недели в МСК (1-7, где 1 - понедельник)"""
    weekday = get_msk_time().weekday() + 1
    return weekday

# ==================== ФУНКЦИЯ УДАЛЕНИЯ ВЕБХУКА ====================
async def delete_webhook():
    temp_bot = Bot(token=BOT_TOKEN)
    await temp_bot.delete_webhook(drop_pending_updates=True)
    await temp_bot.session.close()
    print("✅ Вебхук удален")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Файлы для хранения данных
ADMINS_FILE = "admin.json"
APPLICATIONS_FILE = "applications.json"
INVENTORY_FILE = "inventory.json"
DAILY_BONUS_FILE = "daily_bonus.json"
USERS_FILE = "users.json"  # НОВЫЙ ФАЙЛ: регистрация пользователей
WITHDRAW_FILE = "withdraw_requests.json"  # НОВЫЙ ФАЙЛ: заявки на вывод

# ============== ПОЛНЫЙ СПИСОК МАШИН ИЗ RADMIR ==============
CARS = [
    # ... (весь список машин из предыдущего сообщения, я его сократил для краткости)
    # В реальном коде здесь все машины
]

# ============== ЗАГРУЗКА ДАННЫХ ==============
def load_admins():
    if os.path.exists(ADMINS_FILE):
        try:
            with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
                admins = json.load(f)
                for admin_id, admin_data in admins.items():
                    if 'level' in admin_data:
                        try:
                            admin_data['level'] = int(admin_data['level'])
                        except:
                            admin_data['level'] = 1
                return admins
        except:
            return {str(OWNER_ID): {
                "name": "Главный администратор", 
                "level": OWNER_LEVEL, 
                "added_by": "system",
                "date": get_msk_time().strftime("%Y-%m-%d %H:%M")
            }}
    
    default_admins = {str(OWNER_ID): {
        "name": "Главный администратор", 
        "level": OWNER_LEVEL, 
        "added_by": "system",
        "date": get_msk_time().strftime("%Y-%m-%d %H:%M")
    }}
    save_admins(default_admins)
    return default_admins

def save_admins(admins):
    admins_to_save = {}
    for admin_id, admin_data in admins.items():
        admins_to_save[admin_id] = admin_data.copy()
        if 'level' in admins_to_save[admin_id]:
            admins_to_save[admin_id]['level'] = str(admins_to_save[admin_id]['level'])
    
    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(admins_to_save, f, indent=4, ensure_ascii=False)

def load_applications():
    if os.path.exists(APPLICATIONS_FILE):
        try:
            with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_applications(applications):
    with open(APPLICATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(applications, f, indent=4, ensure_ascii=False)

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        try:
            with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_inventory():
    with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(INVENTORY, f, indent=4, ensure_ascii=False)

def load_daily_bonus():
    if os.path.exists(DAILY_BONUS_FILE):
        try:
            with open(DAILY_BONUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_daily_bonus(data):
    with open(DAILY_BONUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ============== НОВЫЕ ФУНКЦИИ: РЕГИСТРАЦИЯ ==============
def load_users():
    """Загружает данные пользователей (никнеймы в игре)"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users():
    """Сохраняет данные пользователей"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(USERS, f, indent=4, ensure_ascii=False)

def get_user_nickname(user_id):
    """Возвращает никнейм пользователя в игре"""
    return USERS.get(str(user_id), {}).get('nickname')

def is_registered(user_id):
    """Проверяет, зарегистрирован ли пользователь"""
    return str(user_id) in USERS

def register_user(user_id, nickname):
    """Регистрирует пользователя"""
    USERS[str(user_id)] = {
        "nickname": nickname,
        "registered_date": get_msk_time().strftime("%Y-%m-%d %H:%M"),
        "telegram_name": user_full_name
    }
    save_users()

# ============== НОВЫЕ ФУНКЦИИ: ЗАЯВКИ НА ВЫВОД ==============
def load_withdraw_requests():
    """Загружает заявки на вывод предметов"""
    if os.path.exists(WITHDRAW_FILE):
        try:
            with open(WITHDRAW_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_withdraw_requests():
    """Сохраняет заявки на вывод"""
    with open(WITHDRAW_FILE, 'w', encoding='utf-8') as f:
        json.dump(WITHDRAW_REQUESTS, f, indent=4, ensure_ascii=False)

def create_withdraw_request(user_id, item_type, item_data, item_index):
    """Создает заявку на вывод предмета"""
    request_id = str(len(WITHDRAW_REQUESTS) + 1)
    nickname = get_user_nickname(user_id)
    
    WITHDRAW_REQUESTS[request_id] = {
        "id": request_id,
        "user_id": user_id,
        "user_nickname": nickname,
        "telegram_name": USERS.get(str(user_id), {}).get('telegram_name', 'Неизвестно'),
        "item_type": item_type,  # "money" или "car"
        "item_data": item_data,
        "item_index": item_index,
        "status": "pending",  # pending, approved, rejected
        "created_date": get_msk_time().strftime("%Y-%m-%d %H:%M"),
        "processed_by": None,
        "processed_date": None
    }
    save_withdraw_requests()
    return request_id

# Загружаем данные
ADMINS = load_admins()
APPLICATIONS = load_applications()
INVENTORY = load_inventory()
DAILY_BONUS_DATA = load_daily_bonus()
USERS = load_users()
WITHDRAW_REQUESTS = load_withdraw_requests()

# ============== ПРОВЕРКА ПРАВ ==============
def get_admin_level(user_id):
    admin_data = ADMINS.get(str(user_id))
    if admin_data:
        level = admin_data.get('level', 0)
        try:
            return int(level)
        except:
            return 0
    return 0

def is_admin(user_id, min_level=1):
    return get_admin_level(user_id) >= min_level

def is_owner(user_id):
    return get_admin_level(user_id) == OWNER_LEVEL

def get_level_text(level):
    try:
        level = int(level)
    except:
        level = 0
        
    if level == OWNER_LEVEL:
        return "👑 **Владелец** (Уровень 1000)"
    elif level >= 10:
        return f"🔰 **Старший администратор** (Уровень {level})"
    else:
        return f"👨‍💼 **Администратор** (Уровень {level})"

# ============== ФУНКЦИИ ДЛЯ ШАНСОВ ==============
def get_daily_reward_with_chance():
    """
    Возвращает награду с шансами:
    - 40% - 10 рублей
    - 30% - 50 рублей
    - 15% - 150 рублей
    - 15% - машина (случайная)
    """
    roll = random.random() * 100
    
    if roll < 40:
        return {"type": "money", "amount": 10, "name": "💰 10 рублей"}
    elif roll < 70:
        return {"type": "money", "amount": 50, "name": "💰 50 рублей"}
    elif roll < 85:
        return {"type": "money", "amount": 150, "name": "💰 150 рублей"}
    else:
        car = random.choice(CARS)
        rarity_emoji = {
            "common": "⚪", "uncommon": "🟢", "rare": "🔵",
            "epic": "🟣", "legendary": "🟠"
        }.get(car['rarity'], "⚪")
        
        return {
            "type": "car", 
            "car": car,
            "name": f"{rarity_emoji} {car['name']} (ID: {car['id']})"
        }

# ============== ФУНКЦИИ ДЛЯ ИНВЕНТАРЯ ==============
def get_user_inventory(user_id):
    user_id_str = str(user_id)
    if user_id_str not in INVENTORY:
        INVENTORY[user_id_str] = {
            "cars": [],
            "money": 0,
            "items": []
        }
    return INVENTORY[user_id_str]

def add_car_to_inventory(user_id, car):
    user_id_str = str(user_id)
    if user_id_str not in INVENTORY:
        INVENTORY[user_id_str] = {"cars": [], "money": 0, "items": []}
    
    INVENTORY[user_id_str]["cars"].append({
        "id": car["id"],
        "name": car["name"],
        "rarity": car["rarity"],
        "date": get_msk_time().strftime("%Y-%m-%d %H:%M")
    })
    save_inventory()

def add_money_to_inventory(user_id, amount):
    user_id_str = str(user_id)
    if user_id_str not in INVENTORY:
        INVENTORY[user_id_str] = {"cars": [], "money": 0, "items": []}
    
    INVENTORY[user_id_str]["money"] += amount
    save_inventory()

def remove_car_from_inventory(user_id, car_index):
    """Удаляет машину из инвентаря по индексу"""
    user_id_str = str(user_id)
    if user_id_str in INVENTORY:
        cars = INVENTORY[user_id_str].get("cars", [])
        if 0 <= car_index < len(cars):
            removed_car = cars.pop(car_index)
            save_inventory()
            return removed_car
    return None

def remove_money_from_inventory(user_id, amount):
    """Снимает рубли из инвентаря"""
    user_id_str = str(user_id)
    if user_id_str in INVENTORY:
        current_money = INVENTORY[user_id_str].get("money", 0)
        if current_money >= amount:
            INVENTORY[user_id_str]["money"] = current_money - amount
            save_inventory()
            return amount
    return 0

# ============== ФУНКЦИИ ДЛЯ ЕЖЕДНЕВНЫХ НАГРАД ==============
def get_user_daily_data(user_id):
    user_id_str = str(user_id)
    if user_id_str not in DAILY_BONUS_DATA:
        DAILY_BONUS_DATA[user_id_str] = {
            "last_claim_date": None,
            "claimed_days": [],
            "streak": 0,
            "total_claimed": 0
        }
    return DAILY_BONUS_DATA[user_id_str]

def claim_daily_reward(user_id):
    user_id_str = str(user_id)
    today = get_msk_date()
    today_weekday = get_msk_weekday()
    
    if user_id_str not in DAILY_BONUS_DATA:
        DAILY_BONUS_DATA[user_id_str] = {
            "last_claim_date": None,
            "claimed_days": [],
            "streak": 0,
            "total_claimed": 0
        }
    
    user_data = DAILY_BONUS_DATA[user_id_str]
    
    if user_data.get("last_claim_date") == today:
        return {"success": False, "message": "Вы уже получили награду сегодня!"}
    
    reward = get_daily_reward_with_chance()
    
    if reward["type"] == "money":
        add_money_to_inventory(user_id, reward["amount"])
    else:
        add_car_to_inventory(user_id, reward["car"])
    
    user_data["last_claim_date"] = today
    if today_weekday not in user_data.get("claimed_days", []):
        if "claimed_days" not in user_data:
            user_data["claimed_days"] = []
        user_data["claimed_days"].append(today_weekday)
    
    user_data["total_claimed"] = user_data.get("total_claimed", 0) + 1
    
    yesterday = (datetime.now(MSK_TZ) - timedelta(days=1)).strftime("%Y-%m-%d")
    if user_data.get("last_claim_date") == yesterday:
        user_data["streak"] = user_data.get("streak", 0) + 1
    else:
        user_data["streak"] = 1
    
    save_daily_bonus(DAILY_BONUS_DATA)
    
    return {
        "success": True,
        "reward": reward["name"],
        "reward_type": reward["type"],
        "streak": user_data["streak"]
    }

def format_inventory_text(user_id):
    inv = get_user_inventory(user_id)
    
    text = "📦 **ТВОЕ ХРАНИЛИЩЕ**\n\n"
    text += f"💰 **Рубли:** {inv['money']} руб.\n\n"
    
    if inv['cars']:
        text += "🚗 **Твои машины:**\n"
        for i, car in enumerate(inv['cars'], 1):
            rarity_emoji = {
                "common": "⚪", "uncommon": "🟢", "rare": "🔵",
                "epic": "🟣", "legendary": "🟠"
            }.get(car['rarity'], "⚪")
            text += f"{rarity_emoji} {i}. {car['name']} (ID: {car['id']}) - {car['date']}\n"
    else:
        text += "🚗 **Машины:** пока нет\n"
    
    return text, inv

# ============== НАЗВАНИЯ ДНЕЙ ==============
WEEKDAYS = {
    1: "Понедельник", 2: "Вторник", 3: "Среда", 4: "Четверг",
    5: "Пятница", 6: "Суббота", 7: "Воскресенье"
}

# ============== СОСТОЯНИЯ ==============
class RegistrationForm(StatesGroup):
    waiting_for_nickname = State()

class WithdrawForm(StatesGroup):
    choosing_item = State()
    confirming = State()

class AdminApplyForm(StatesGroup):
    waiting_for_age = State()
    waiting_for_experience = State()
    waiting_for_reason = State()

class AddAdminForm(StatesGroup):
    waiting_for_id = State()
    waiting_for_name = State()
    waiting_for_level = State()

class AdminApplicationForm(StatesGroup):
    waiting_for_accept_text = State()

class AdminWithdrawForm(StatesGroup):
    waiting_for_request_id = State()
    waiting_for_reply = State()

# ============== КЛАВИАТУРЫ ==============
def get_main_keyboard(user_id=None):
    buttons = [
        [InlineKeyboardButton(text="📝 Регистрация", callback_data="register")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="▶️ Начать играть", callback_data="start_play")],
        [InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral")],
        [InlineKeyboardButton(text="🎁 Получение бонусов", callback_data="bonuses")],
        [InlineKeyboardButton(text="🏆 Ежедневные награды", callback_data="daily_rewards")],
        [InlineKeyboardButton(text="📦 Хранилище", callback_data="inventory")],
        [InlineKeyboardButton(text="📝 Подать заявку на админа", callback_data="apply_admin")],
    ]
    
    if user_id and is_admin(user_id):
        buttons.append([InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel")])
    
    keyboard = []
    row = []
    for button in buttons:
        row.append(button[0])
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_inventory_keyboard(user_id):
    """Клавиатура для хранилища с возможностью вывода"""
    inv = get_user_inventory(user_id)
    buttons = []
    
    # Кнопки для вывода рублей
    if inv['money'] > 0:
        buttons.append([InlineKeyboardButton(text=f"💰 Вывести {inv['money']} руб.", callback_data="withdraw_money")])
    
    # Кнопки для вывода машин
    for i, car in enumerate(inv['cars']):
        rarity_emoji = {
            "common": "⚪", "uncommon": "🟢", "rare": "🔵",
            "epic": "🟣", "legendary": "🟠"
        }.get(car['rarity'], "⚪")
        buttons.append([InlineKeyboardButton(
            text=f"{rarity_emoji} Вывести: {car['name']}", 
            callback_data=f"withdraw_car_{i}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_keyboard(user_level):
    buttons = [
        [InlineKeyboardButton(text="👥 Список админов", callback_data="admin_list")],
        [InlineKeyboardButton(text="📝 Заявки в админы", callback_data="admin_applications")],
        [InlineKeyboardButton(text="📋 Заявки на вывод", callback_data="admin_withdraw_requests")],
    ]
    
    if user_level >= 10:
        buttons.append([InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_withdraw_requests_keyboard():
    """Клавиатура для списка заявок на вывод"""
    buttons = []
    pending = [req for req in WITHDRAW_REQUESTS.values() if req['status'] == 'pending']
    
    for req in pending[:10]:
        user_name = req.get('telegram_name', 'Неизвестно')
        item_info = f"{req['item_data'].get('name', 'Предмет')}" if req['item_type'] == 'car' else f"{req['item_data']} руб."
        buttons.append([InlineKeyboardButton(
            text=f"#{req['id']} - {user_name}: {item_info}",
            callback_data=f"view_withdraw_{req['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_withdraw_action_keyboard(request_id):
    """Клавиатура для действий с заявкой на вывод"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Выдано", callback_data=f"withdraw_approve_{request_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"withdraw_reject_{request_id}")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_withdraw_requests")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ============== ОБРАБОТЧИКИ ==============
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name
    
    welcome_text = f"""
🌟 Добро пожаловать в **VORTEX CRMP**! 🌟

Привет, {user_name}!

Выберите действие в меню ниже:
    """
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(message.from_user.id),
        parse_mode="Markdown"
    )
    logger.info(f"Пользователь {message.from_user.id} запустил бота")

# ============== РЕГИСТРАЦИЯ ==============
@dp.callback_query(F.data == "register")
async def register_start(callback: CallbackQuery, state: FSMContext):
    if is_registered(callback.from_user.id):
        nickname = get_user_nickname(callback.from_user.id)
        await callback.message.edit_text(
            f"✅ Вы уже зарегистрированы!\n\nВаш никнейм в игре: **{nickname}**",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
            ),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📝 **Регистрация**\n\n"
        "Введите ваш никнейм в игре Radmir:\n"
        "(Тот, под которым вы играете на сервере)",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_main")]]
        ),
        parse_mode="Markdown"
    )
    await state.set_state(RegistrationForm.waiting_for_nickname)
    await callback.answer()

@dp.message(RegistrationForm.waiting_for_nickname)
async def register_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    
    if len(nickname) < 3 or len(nickname) > 20:
        await message.answer("❌ Никнейм должен быть от 3 до 20 символов. Попробуйте еще раз:")
        return
    
    # Проверяем, не занят ли никнейм
    for uid, user_data in USERS.items():
        if user_data.get('nickname', '').lower() == nickname.lower():
            await message.answer("❌ Этот никнейм уже занят. Введите другой:")
            return
    
    # Регистрируем пользователя
    USERS[str(message.from_user.id)] = {
        "nickname": nickname,
        "registered_date": get_msk_time().strftime("%Y-%m-%d %H:%M"),
        "telegram_name": message.from_user.full_name
    }
    save_users()
    
    await message.answer(
        f"✅ **Регистрация успешна!**\n\n"
        f"Ваш никнейм: **{nickname}**\n\n"
        f"Теперь вы можете получать награды и выводить их в игру!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_main")]]
        ),
        parse_mode="Markdown"
    )
    await state.clear()

# ============== ХРАНИЛИЩЕ И ВЫВОД ==============
@dp.callback_query(F.data == "inventory")
async def show_inventory(callback: CallbackQuery):
    if not is_registered(callback.from_user.id):
        await callback.message.edit_text(
            "❌ Сначала нужно зарегистрироваться!\n\nНажмите кнопку 'Регистрация' в главном меню.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
            )
        )
        await callback.answer()
        return
    
    text, inv = format_inventory_text(callback.from_user.id)
    
    if inv['cars'] or inv['money'] > 0:
        text += "\n\n👇 Нажмите на предмет, чтобы подать заявку на вывод в игру"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_inventory_keyboard(callback.from_user.id),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "withdraw_money")
async def withdraw_money(callback: CallbackQuery):
    if not is_registered(callback.from_user.id):
        await callback.answer("❌ Сначала зарегистрируйтесь!", show_alert=True)
        return
    
    inv = get_user_inventory(callback.from_user.id)
    amount = inv['money']
    nickname = get_user_nickname(callback.from_user.id)
    
    if amount <= 0:
        await callback.answer("❌ У вас нет рублей для вывода!", show_alert=True)
        return
    
    # Создаем заявку
    request_id = create_withdraw_request(
        callback.from_user.id,
        "money",
        amount,
        None
    )
    
    # Уведомляем админов
    for admin_id in ADMINS.keys():
        if get_admin_level(int(admin_id)) >= 1:
            try:
                await bot.send_message(
                    int(admin_id),
                    f"💰 **Новая заявка на вывод #{request_id}**\n\n"
                    f"👤 **Пользователь:** {callback.from_user.full_name}\n"
                    f"🆔 **Telegram ID:** {callback.from_user.id}\n"
                    f"🎮 **Ник в игре:** {nickname}\n"
                    f"💵 **Сумма:** {amount} руб.\n\n"
                    f"Для обработки зайдите в админ-панель",
                    parse_mode="Markdown"
                )
            except:
                pass
    
    await callback.message.edit_text(
        f"✅ **Заявка на вывод #{request_id} создана!**\n\n"
        f"💰 Сумма: {amount} руб.\n"
        f"🎮 Ваш ник: {nickname}\n\n"
        f"Администратор рассмотрит заявку и выдаст вам предметы в игре.\n"
        f"Вы получите уведомление, когда заявка будет обработана.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 В хранилище", callback_data="inventory")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("withdraw_car_"))
async def withdraw_car(callback: CallbackQuery):
    if not is_registered(callback.from_user.id):
        await callback.answer("❌ Сначала зарегистрируйтесь!", show_alert=True)
        return
    
    car_index = int(callback.data.split("_")[2])
    inv = get_user_inventory(callback.from_user.id)
    nickname = get_user_nickname(callback.from_user.id)
    
    if car_index >= len(inv['cars']):
        await callback.answer("❌ Машина не найдена!", show_alert=True)
        return
    
    car = inv['cars'][car_index]
    
    # Создаем заявку
    request_id = create_withdraw_request(
        callback.from_user.id,
        "car",
        car,
        car_index
    )
    
    # Уведомляем админов
    for admin_id in ADMINS.keys():
        if get_admin_level(int(admin_id)) >= 1:
            try:
                await bot.send_message(
                    int(admin_id),
                    f"🚗 **Новая заявка на вывод #{request_id}**\n\n"
                    f"👤 **Пользователь:** {callback.from_user.full_name}\n"
                    f"🆔 **Telegram ID:** {callback.from_user.id}\n"
                    f"🎮 **Ник в игре:** {nickname}\n"
                    f"🚘 **Машина:** {car['name']} (ID: {car['id']})\n\n"
                    f"Для обработки зайдите в админ-панель",
                    parse_mode="Markdown"
                )
            except:
                pass
    
    await callback.message.edit_text(
        f"✅ **Заявка на вывод #{request_id} создана!**\n\n"
        f"🚘 Машина: {car['name']} (ID: {car['id']})\n"
        f"🎮 Ваш ник: {nickname}\n\n"
        f"Администратор рассмотрит заявку и выдаст вам предметы в игре.\n"
        f"Вы получите уведомление, когда заявка будет обработана.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 В хранилище", callback_data="inventory")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============== АДМИН-ПАНЕЛЬ: ЗАЯВКИ НА ВЫВОД ==============
@dp.callback_query(F.data == "admin_withdraw_requests")
async def admin_withdraw_requests(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    pending = [req for req in WITHDRAW_REQUESTS.values() if req['status'] == 'pending']
    
    if not pending:
        await callback.message.edit_text(
            "📋 Нет ожидающих заявок на вывод",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]]
            )
        )
        await callback.answer()
        return
    
    text = f"📋 **Заявки на вывод**\n\nВсего ожидает: {len(pending)}\n\n"
    for req in pending[:5]:
        item_info = f"{req['item_data'].get('name', 'Предмет')}" if req['item_type'] == 'car' else f"{req['item_data']} руб."
        text += f"#{req['id']} - {req['telegram_name']} ({req['user_nickname']}): {item_info}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_withdraw_requests_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("view_withdraw_"))
async def view_withdraw_request(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    request_id = callback.data.replace("view_withdraw_", "")
    req = WITHDRAW_REQUESTS.get(request_id)
    
    if not req:
        await callback.answer("❌ Заявка не найдена!", show_alert=True)
        return
    
    if req['item_type'] == 'money':
        item_text = f"💰 **Сумма:** {req['item_data']} руб."
    else:
        item_text = f"🚗 **Машина:** {req['item_data']['name']} (ID: {req['item_data']['id']})"
    
    text = f"""
📋 **Заявка на вывод #{request_id}**

👤 **Пользователь:** {req['telegram_name']}
🆔 **Telegram ID:** {req['user_id']}
🎮 **Ник в игре:** {req['user_nickname']}
📅 **Дата заявки:** {req['created_date']}
📌 **Статус:** {req['status']}

{item_text}

---
✅ Нажмите "Выдано", когда выдадите предмет в игре
❌ Нажмите "Отклонить", чтобы отклонить заявку
    """
    
    await callback.message.edit_text(
        text,
        reply_markup=get_withdraw_action_keyboard(request_id),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("withdraw_approve_"))
async def approve_withdraw(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    request_id = callback.data.replace("withdraw_approve_", "")
    req = WITHDRAW_REQUESTS.get(request_id)
    
    if not req:
        await callback.answer("❌ Заявка не найдена!", show_alert=True)
        return
    
    # Обновляем статус заявки
    req['status'] = 'approved'
    req['processed_by'] = callback.from_user.full_name
    req['processed_date'] = get_msk_time().strftime("%Y-%m-%d %H:%M")
    save_withdraw_requests()
    
    # Удаляем предмет из инвентаря
    if req['item_type'] == 'money':
        remove_money_from_inventory(req['user_id'], req['item_data'])
    else:
        remove_car_from_inventory(req['user_id'], req['item_index'])
    
    # Уведомляем пользователя
    try:
        if req['item_type'] == 'money':
            item_text = f"💰 {req['item_data']} руб."
        else:
            item_text = f"🚗 {req['item_data']['name']}"
        
        await bot.send_message(
            req['user_id'],
            f"✅ **Ваша заявка на вывод #{request_id} одобрена!**\n\n"
            f"{item_text} успешно выданы в игре!\n"
            f"Проверьте свой аккаунт на сервере.",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await callback.message.edit_text(
        f"✅ Заявка #{request_id} отмечена как выданная!\n\nПользователь уведомлен.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 К заявкам", callback_data="admin_withdraw_requests")]]
        )
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("withdraw_reject_"))
async def reject_withdraw(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    request_id = callback.data.replace("withdraw_reject_", "")
    req = WITHDRAW_REQUESTS.get(request_id)
    
    if not req:
        await callback.answer("❌ Заявка не найдена!", show_alert=True)
        return
    
    # Обновляем статус заявки
    req['status'] = 'rejected'
    req['processed_by'] = callback.from_user.full_name
    req['processed_date'] = get_msk_time().strftime("%Y-%m-%d %H:%M")
    save_withdraw_requests()
    
    # Уведомляем пользователя
    try:
        if req['item_type'] == 'money':
            item_text = f"💰 {req['item_data']} руб."
        else:
            item_text = f"🚗 {req['item_data']['name']}"
        
        await bot.send_message(
            req['user_id'],
            f"❌ **Ваша заявка на вывод #{request_id} отклонена.**\n\n"
            f"Предмет: {item_text}\n"
            f"Обратитесь к администратору для уточнения причины.",
            parse_mode="Markdown"
        )
    except:
        pass
    
    await callback.message.edit_text(
        f"❌ Заявка #{request_id} отклонена.\n\nПользователь уведомлен.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 К заявкам", callback_data="admin_withdraw_requests")]]
        )
    )
    await callback.answer()

# Остальные обработчики (stats, start_play, referral, bonuses, daily_rewards, claim_daily,
# apply_admin, admin_panel, admin_list, admin_add и т.д.) остаются без изменений
# Я их опустил для краткости, но в полном файле они должны быть

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📌 **Главное меню:**",
        reply_markup=get_main_keyboard(callback.from_user.id),
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer()

# ============== ЗАПУСК ==============
async def main():
    print("🚀 Бот запущен и готов к работе!")
    print(f"👑 Владелец ID: {OWNER_ID}")
    print(f"👥 Администраторов: {len(ADMINS)}")
    print(f"👤 Зарегистрировано пользователей: {len(USERS)}")
    print(f"📦 Всего машин: {len(CARS)}")
    
    await delete_webhook()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
