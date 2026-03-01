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
    return datetime.now(MSK_TZ)

def get_msk_date():
    return get_msk_time().strftime("%Y-%m-%d")

def get_msk_weekday():
    weekday = get_msk_time().weekday() + 1
    return weekday

# ==================== ФУНКЦИИ ДЛЯ УСТРАНЕНИЯ КОНФЛИКТОВ ====================
async def force_stop_all_instances():
    try:
        temp_bot = Bot(token=BOT_TOKEN)
        await temp_bot.delete_webhook(drop_pending_updates=True)
        await temp_bot.session.close()
        print("✅ Все конфликтующие экземпляры бота остановлены")
    except Exception as e:
        print(f"⚠️ Ошибка при остановке конфликтов: {e}")

async def delete_webhook():
    try:
        temp_bot = Bot(token=BOT_TOKEN)
        await temp_bot.delete_webhook(drop_pending_updates=True)
        await temp_bot.session.close()
        print("✅ Вебхук удален")
    except Exception as e:
        print(f"⚠️ Ошибка при удалении вебхука: {e}")

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
USERS_FILE = "users.json"
WITHDRAW_FILE = "withdraw_requests.json"

# ============== СПИСОК МАШИН ==============
CARS = [
    {"id": 15065, "name": "Toyota Chaser", "rarity": "rare"},
    {"id": 15066, "name": "Volkswagen Touareg", "rarity": "common"},
    {"id": 15067, "name": "BMW E38 740", "rarity": "common"},
    {"id": 15068, "name": "Toyota Mark 2", "rarity": "common"},
    {"id": 15069, "name": "Toyota Camry V50", "rarity": "common"},
    {"id": 15070, "name": "УАЗ Буханка", "rarity": "common"},
    {"id": 15071, "name": "Lexus LX570", "rarity": "rare"},
    {"id": 15072, "name": "Lexus IS200", "rarity": "common"},
    {"id": 15073, "name": "BMW 740 F02", "rarity": "rare"},
    {"id": 15074, "name": "Lada 2114", "rarity": "common"},
    {"id": 15075, "name": "Jeep Grand Cherokee Trackhawk", "rarity": "epic"},
    {"id": 15076, "name": "Cadillac Escalade", "rarity": "rare"},
    {"id": 15077, "name": "Honda Accord", "rarity": "common"},
    {"id": 15078, "name": "Lada 2110", "rarity": "common"},
    {"id": 15079, "name": "Lada 2104", "rarity": "common"},
    {"id": 15080, "name": "ВАЗ 2105", "rarity": "common"},
    {"id": 15081, "name": "Volkswagen Scirocco", "rarity": "common"},
    {"id": 15082, "name": "Mercedes-Benz 560 SEC", "rarity": "rare"},
    {"id": 15083, "name": "ГАЗ 66 'ШИШИГА'", "rarity": "uncommon"},
    {"id": 15084, "name": "Alfa Romeo 155", "rarity": "common"},
    {"id": 15085, "name": "BUGATTI CHIRON", "rarity": "legendary"},
    {"id": 15086, "name": "Lexus IS F", "rarity": "epic"},
    {"id": 15087, "name": "Mazda 3 MPS", "rarity": "uncommon"},
    {"id": 15088, "name": "Mazda MX-5", "rarity": "uncommon"},
    {"id": 15089, "name": "AUDI RS7", "rarity": "epic"},
    {"id": 15090, "name": "Nissan Silvia S15", "rarity": "rare"},
    {"id": 15091, "name": "Mercedes-Benz 300 SL", "rarity": "legendary"},
    {"id": 15092, "name": "VOLVO XC90", "rarity": "rare"},
    {"id": 15093, "name": "Mercedes-Benz W124 E", "rarity": "common"},
    {"id": 15094, "name": "BMW X6M F16", "rarity": "epic"},
    {"id": 15095, "name": "Mercedes-Benz Actros", "rarity": "uncommon"},
    {"id": 15096, "name": "Volvo FH16", "rarity": "uncommon"},
    {"id": 15097, "name": "Камаз Volvo", "rarity": "uncommon"},
    {"id": 15098, "name": "Kaмаз 54115", "rarity": "uncommon"},
    {"id": 15099, "name": "МАЗ", "rarity": "uncommon"},
    {"id": 15100, "name": "Scania R700", "rarity": "rare"},
    {"id": 15101, "name": "ЗИЛ 130 (тягач)", "rarity": "common"},
    {"id": 15102, "name": "MAN TGS", "rarity": "uncommon"},
    {"id": 15103, "name": "ЗИЛ 131", "rarity": "common"},
    {"id": 15104, "name": "Tesla Cybertruck", "rarity": "epic"},
    # ... здесь остальные машины (для краткости сократил)
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

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users():
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(USERS, f, indent=4, ensure_ascii=False)

def load_withdraw_requests():
    if os.path.exists(WITHDRAW_FILE):
        try:
            with open(WITHDRAW_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_withdraw_requests():
    with open(WITHDRAW_FILE, 'w', encoding='utf-8') as f:
        json.dump(WITHDRAW_REQUESTS, f, indent=4, ensure_ascii=False)

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
    user_id_str = str(user_id)
    if user_id_str in INVENTORY:
        cars = INVENTORY[user_id_str].get("cars", [])
        if 0 <= car_index < len(cars):
            removed_car = cars.pop(car_index)
            save_inventory()
            return removed_car
    return None

def remove_money_from_inventory(user_id, amount):
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
    
    # ✅ ПРОВЕРКА: получал ли уже сегодня
    if user_data.get("last_claim_date") == today:
        return {"success": False, "message": "❌ Вы уже получили награду сегодня!\nЗаходите завтра!"}
    
    reward = get_daily_reward_with_chance()
    
    if reward["type"] == "money":
        add_money_to_inventory(user_id, reward["amount"])
    else:
        add_car_to_inventory(user_id, reward["car"])
    
    # ✅ Обновляем данные
    user_data["last_claim_date"] = today
    if today_weekday not in user_data.get("claimed_days", []):
        if "claimed_days" not in user_data:
            user_data["claimed_days"] = []
        user_data["claimed_days"].append(today_weekday)
    
    user_data["total_claimed"] = user_data.get("total_claimed", 0) + 1
    
    # ✅ Обновляем streak
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

class AddAdminForm(StatesGroup):
    waiting_for_id = State()
    waiting_for_name = State()
    waiting_for_level = State()

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

def get_inventory_keyboard(user_id, pending_requests):
    inv = get_user_inventory(user_id)
    buttons = []
    
    # ✅ Проверяем, есть ли уже заявка на вывод рублей
    has_pending_money = any(
        req['item_type'] == 'money' and req['status'] == 'pending' 
        for req in pending_requests
    )
    
    if inv['money'] > 0 and not has_pending_money:
        buttons.append([InlineKeyboardButton(text=f"💰 Вывести {inv['money']} руб.", callback_data="withdraw_money")])
    elif inv['money'] > 0 and has_pending_money:
        buttons.append([InlineKeyboardButton(text=f"⏳ Заявка на {inv['money']} руб. уже в обработке", callback_data="noop")])
    
    # ✅ Проверяем для каждой машины, есть ли уже заявка
    for i, car in enumerate(inv['cars']):
        has_pending_car = any(
            req['item_type'] == 'car' and 
            req['item_index'] == i and 
            req['status'] == 'pending'
            for req in pending_requests
        )
        
        rarity_emoji = {
            "common": "⚪", "uncommon": "🟢", "rare": "🔵",
            "epic": "🟣", "legendary": "🟠"
        }.get(car['rarity'], "⚪")
        
        if not has_pending_car:
            buttons.append([InlineKeyboardButton(
                text=f"{rarity_emoji} Вывести: {car['name']}", 
                callback_data=f"withdraw_car_{i}"
            )])
        else:
            buttons.append([InlineKeyboardButton(
                text=f"⏳ {car['name']} (заявка в обработке)", 
                callback_data="noop"
            )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_keyboard(user_level):
    buttons = [
        [InlineKeyboardButton(text="👥 Список админов", callback_data="admin_list")],
        [InlineKeyboardButton(text="📋 Заявки на вывод", callback_data="admin_withdraw_requests")],
    ]
    
    if user_level >= 10:
        buttons.append([InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_withdraw_requests_keyboard():
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

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📌 **Главное меню:**",
        reply_markup=get_main_keyboard(callback.from_user.id),
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer()

# ============== РЕГИСТРАЦИЯ ==============
def is_registered(user_id):
    return str(user_id) in USERS

def get_user_nickname(user_id):
    return USERS.get(str(user_id), {}).get('nickname')

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
    
    # ✅ Проверяем уникальность ника
    for uid, user_data in USERS.items():
        if user_data.get('nickname', '').lower() == nickname.lower():
            await message.answer("❌ Этот никнейм уже занят. Введите другой:")
            return
    
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
def get_user_pending_requests(user_id):
    """Возвращает список ожидающих заявок пользователя"""
    return [
        req for req in WITHDRAW_REQUESTS.values() 
        if req['user_id'] == user_id and req['status'] == 'pending'
    ]

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
    
    # ✅ Получаем ожидающие заявки
    pending_requests = get_user_pending_requests(callback.from_user.id)
    
    if pending_requests:
        text += "\n\n⏳ **У вас есть заявки в обработке:**\n"
        for req in pending_requests:
            if req['item_type'] == 'money':
                text += f"• 💰 {req['item_data']} руб.\n"
            else:
                text += f"• 🚗 {req['item_data']['name']}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_inventory_keyboard(callback.from_user.id, pending_requests),
        parse_mode="Markdown"
    )
    await callback.answer()

def create_withdraw_request(user_id, item_type, item_data, item_index):
    request_id = str(len(WITHDRAW_REQUESTS) + 1)
    nickname = get_user_nickname(user_id)
    
    WITHDRAW_REQUESTS[request_id] = {
        "id": request_id,
        "user_id": user_id,
        "user_nickname": nickname,
        "telegram_name": USERS.get(str(user_id), {}).get('telegram_name', 'Неизвестно'),
        "item_type": item_type,
        "item_data": item_data,
        "item_index": item_index,
        "status": "pending",
        "created_date": get_msk_time().strftime("%Y-%m-%d %H:%M"),
        "processed_by": None,
        "processed_date": None
    }
    save_withdraw_requests()
    return request_id

@dp.callback_query(F.data == "withdraw_money")
async def withdraw_money(callback: CallbackQuery):
    if not is_registered(callback.from_user.id):
        await callback.answer("❌ Сначала зарегистрируйтесь!", show_alert=True)
        return
    
    # ✅ Проверяем, нет ли уже заявки на рубли
    pending_requests = get_user_pending_requests(callback.from_user.id)
    has_pending_money = any(req['item_type'] == 'money' for req in pending_requests)
    
    if has_pending_money:
        await callback.answer("❌ У вас уже есть заявка на вывод рублей в обработке!", show_alert=True)
        return
    
    inv = get_user_inventory(callback.from_user.id)
    amount = inv['money']
    nickname = get_user_nickname(callback.from_user.id)
    
    if amount <= 0:
        await callback.answer("❌ У вас нет рублей для вывода!", show_alert=True)
        return
    
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
        f"Вы получите уведомление, когда заявка будет обработана.\n\n"
        f"⚠️ Повторная заявка на этот предмет станет доступна после обработки текущей.",
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
    
    # ✅ Проверяем, нет ли уже заявки на эту машину
    pending_requests = get_user_pending_requests(callback.from_user.id)
    has_pending_car = any(
        req['item_type'] == 'car' and req['item_index'] == car_index 
        for req in pending_requests
    )
    
    if has_pending_car:
        await callback.answer("❌ На эту машину уже есть заявка в обработке!", show_alert=True)
        return
    
    inv = get_user_inventory(callback.from_user.id)
    nickname = get_user_nickname(callback.from_user.id)
    
    if car_index >= len(inv['cars']):
        await callback.answer("❌ Машина не найдена!", show_alert=True)
        return
    
    car = inv['cars'][car_index]
    
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
        f"Вы получите уведомление, когда заявка будет обработана.\n\n"
        f"⚠️ Повторная заявка на этот предмет станет доступна после обработки текущей.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 В хранилище", callback_data="inventory")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    """Заглушка для неактивных кнопок"""
    await callback.answer("⏳ Эта заявка уже в обработке", show_alert=True)

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
    
    req['status'] = 'approved'
    req['processed_by'] = callback.from_user.full_name
    req['processed_date'] = get_msk_time().strftime("%Y-%m-%d %H:%M")
    save_withdraw_requests()
    
    if req['item_type'] == 'money':
        remove_money_from_inventory(req['user_id'], req['item_data'])
    else:
        remove_car_from_inventory(req['user_id'], req['item_index'])
    
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
    
    req['status'] = 'rejected'
    req['processed_by'] = callback.from_user.full_name
    req['processed_date'] = get_msk_time().strftime("%Y-%m-%d %H:%M")
    save_withdraw_requests()
    
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

# ============== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ ==============
@dp.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    inv = get_user_inventory(user_id)
    daily = get_user_daily_data(user_id)
    
    text = f"""
📊 **Ваша статистика:**

👤 Профиль: {callback.from_user.full_name}
🆔 ID: {user_id}

💰 Рубли: {inv['money']}
🚗 Машин: {len(inv['cars'])}
🏆 Всего наград: {daily.get('total_claimed', 0)}
🔥 Серия: {daily.get('streak', 0)} дней
    """
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "start_play")
async def start_play(callback: CallbackQuery):
    await callback.message.edit_text(
        "▶️ **Начать играть**\n\n"
        "Присоединяйся к нам!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📱 Перейти к посту", url="https://t.me/vortex_gta/132")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "referral")
async def show_referral(callback: CallbackQuery):
    ref_link = f"https://t.me/{(await bot.me()).username}?start=ref_{callback.from_user.id}"
    
    text = f"""
👥 **Реферальная система**

🔗 Твоя ссылка:
`{ref_link}`

👥 Рефералов: 0
    """
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "bonuses")
async def show_bonuses(callback: CallbackQuery):
    text = """
🎁 **Получение бонусов**

Доступные бонусы:

✅ **Ежедневные награды** - заходи каждый день
✅ **Реферальный бонус** - приглашай друзей

В ежедневных наградах ты можешь получить:
• 💰 10 рублей (40% шанс)
• 💰 50 рублей (30% шанс)
• 💰 150 рублей (15% шанс)
• 🚗 Редкие машины (15% шанс)
    """
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏆 Получить награду", callback_data="daily_rewards")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "daily_rewards")
async def show_daily_rewards(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = get_user_daily_data(user_id)
    today_weekday = get_msk_weekday()
    
    claimed_today = (user_data.get("last_claim_date") == get_msk_date())
    
    text = "🏆 **Ежедневные подарки**\n"
    text += "Заходи каждый день и забирай новую награду\n\n"
    
    for day in range(1, 8):
        status = "✅ Получено" if day in user_data.get("claimed_days", []) else "❌ Не получено"
        text += f"{day}. {WEEKDAYS[day]} - {status}\n"
    
    text += "\n"
    
    short_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for i, day in enumerate(range(1, 8), 1):
        text += f"{day}. {short_names[i-1]}  "
    
    text += "\n\n"
    
    main_prize_status = "✅ Получено" if 7 in user_data.get("claimed_days", []) else "❌ Не получено"
    text += f"ГЛАВНЫЙ ПРИЗ - {main_prize_status}\n\n"
    
    text += f"📅 Сегодня: {WEEKDAYS[today_weekday]}"
    if claimed_today:
        text += " (уже получено)"
    
    buttons = []
    if not claimed_today:
        buttons.append([InlineKeyboardButton(text="🎁 Забрать награду", callback_data="claim_daily")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "claim_daily")
async def claim_daily(callback: CallbackQuery):
    user_id = callback.from_user.id
    result = claim_daily_reward(user_id)
    
    if result["success"]:
        text = f"""
✅ **Награда получена!**

🎁 Ты получил: **{result['reward']}**
🔥 Текущая серия: {result['streak']} дней

Заходи завтра за новой наградой!
        """
    else:
        text = f"""
❌ **{result['message']}**

Сегодня: {WEEKDAYS[get_msk_weekday()]}
Заходи завтра!
        """
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏆 К наградам", callback_data="daily_rewards")],
                [InlineKeyboardButton(text="📦 В хранилище", callback_data="inventory")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============== АДМИН-ПАНЕЛЬ ==============
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    user_level = get_admin_level(callback.from_user.id)
    
    if user_level == 0:
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"⚙️ **Админ-панель**\n\n{get_level_text(user_level)}\n\nВыберите действие:",
        reply_markup=get_admin_keyboard(user_level),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    user_level = get_admin_level(message.from_user.id)
    
    if user_level == 0:
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    
    await message.answer(
        f"⚙️ **Админ-панель**\n\n{get_level_text(user_level)}\n\nВыберите действие:",
        reply_markup=get_admin_keyboard(user_level),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "admin_list")
async def show_admin_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return
    
    text = "👥 **Список администраторов:**\n\n"
    for admin_id, data in ADMINS.items():
        level = data.get('level', 0)
        if str(admin_id) == str(OWNER_ID):
            text += f"👑 **{data['name']}** (ур.{level}) - `{admin_id}`\n"
        elif level >= 10:
            text += f"🔰 **{data['name']}** (ур.{level}) - `{admin_id}`\n"
        else:
            text += f"• {data['name']} (ур.{level}) - `{admin_id}`\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_add")
async def admin_add_start(callback: CallbackQuery, state: FSMContext):
    if get_admin_level(callback.from_user.id) < 10:
        await callback.answer("❌ Только админы 10+ могут добавлять!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "➕ **Добавление администратора**\n\nВведите Telegram ID:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_panel")]]
        )
    )
    await state.set_state(AddAdminForm.waiting_for_id)
    await callback.answer()

@dp.message(AddAdminForm.waiting_for_id)
async def process_add_admin_id(message: types.Message, state: FSMContext):
    try:
        new_id = int(message.text.strip())
        if str(new_id) in ADMINS:
            await message.answer("❌ Уже администратор!")
            await state.clear()
            return
        
        await state.update_data(new_admin_id=new_id)
        await message.answer("✏️ Введите имя:")
        await state.set_state(AddAdminForm.waiting_for_name)
    except:
        await message.answer("❌ Введите корректный ID (только цифры)!")

@dp.message(AddAdminForm.waiting_for_name)
async def process_add_admin_name(message: types.Message, state: FSMContext):
    await state.update_data(admin_name=message.text.strip())
    user_level = get_admin_level(message.from_user.id)
    max_level = user_level - 1
    await message.answer(f"📊 Введите уровень (1-{max_level}):")
    await state.set_state(AddAdminForm.waiting_for_level)

@dp.message(AddAdminForm.waiting_for_level)
async def process_add_admin_level(message: types.Message, state: FSMContext):
    try:
        level = int(message.text.strip())
        user_level = get_admin_level(message.from_user.id)
        
        if level < 1 or level >= user_level:
            await message.answer(f"❌ Уровень должен быть от 1 до {user_level-1}!")
            return
        
        data = await state.get_data()
        new_id = data['new_admin_id']
        name = data['admin_name']
        
        ADMINS[str(new_id)] = {
            "name": name,
            "level": level,
            "added_by": message.from_user.full_name,
            "date": get_msk_time().strftime("%Y-%m-%d %H:%M")
        }
        
        save_admins(ADMINS)
        
        try:
            await bot.send_message(
                new_id,
                f"✅ Вы стали администратором!\nУровень: {level}"
            )
        except:
            pass
        
        await message.answer(f"✅ Администратор {name} добавлен с уровнем {level}!")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите число!")

# ============== ЗАПУСК ==============
async def main():
    print("🚀 Бот запущен и готов к работе!")
    print(f"👑 Владелец ID: {OWNER_ID}")
    print(f"👥 Администраторов: {len(ADMINS)}")
    print(f"👤 Зарегистрировано пользователей: {len(USERS)}")
    print(f"📦 Всего машин: {len(CARS)}")
    
    # Принудительно останавливаем все другие экземпляры
    await force_stop_all_instances()
    await asyncio.sleep(2)
    
    # Удаляем вебхук
    await delete_webhook()
    await asyncio.sleep(1)
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
