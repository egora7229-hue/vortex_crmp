import asyncio
import logging
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime, timedelta
import random

# ==================== ТВОИ ДАННЫЕ ====================
BOT_TOKEN = "8640012758:AAFhVeVAleSvtg36-dFbaYxUY5Zl8o-9_ck"
OWNER_ID = 7470989833
OWNER_LEVEL = 1000

# ==================== ФУНКЦИЯ УДАЛЕНИЯ ВЕБХУКА ====================
async def delete_webhook():
    """Удаляет вебхук перед запуском polling"""
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
ADMINS_FILE = "admins.json"
APPLICATIONS_FILE = "applications.json"
INVENTORY_FILE = "inventory.json"
DAILY_BONUS_FILE = "daily_bonus.json"

# ============== ЗАГРУЗКА/СОХРАНЕНИЕ ДАННЫХ ==============
def load_admins():
    """Загружает список админов из файла"""
    if os.path.exists(ADMINS_FILE):
        try:
            with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
                admins = json.load(f)
                for admin_id, admin_data in admins.items():
                    if 'level' in admin_data:
                        try:
                            admin_data['level'] = int(admin_data['level'])
                        except (ValueError, TypeError):
                            admin_data['level'] = 1
                return admins
        except:
            return {str(OWNER_ID): {
                "name": "Главный администратор", 
                "level": OWNER_LEVEL, 
                "added_by": "system",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            }}
    return {str(OWNER_ID): {
        "name": "Главный администратор", 
        "level": OWNER_LEVEL, 
        "added_by": "system",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }}

def save_admins(admins):
    """Сохраняет список админов в файл"""
    admins_to_save = {}
    for admin_id, admin_data in admins.items():
        admins_to_save[admin_id] = admin_data.copy()
        if 'level' in admins_to_save[admin_id]:
            admins_to_save[admin_id]['level'] = str(admins_to_save[admin_id]['level'])
    
    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(admins_to_save, f, indent=4, ensure_ascii=False)

def load_applications():
    """Загружает заявки в админы"""
    if os.path.exists(APPLICATIONS_FILE):
        try:
            with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_applications(applications):
    """Сохраняет заявки в админы"""
    with open(APPLICATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(applications, f, indent=4, ensure_ascii=False)

def load_inventory():
    """Загружает инвентарь пользователей"""
    if os.path.exists(INVENTORY_FILE):
        try:
            with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_inventory(inventory):
    """Сохраняет инвентарь пользователей"""
    with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=4, ensure_ascii=False)

def load_daily_bonus():
    """Загружает данные о ежедневных бонусах"""
    if os.path.exists(DAILY_BONUS_FILE):
        try:
            with open(DAILY_BONUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_daily_bonus(data):
    """Сохраняет данные о ежедневных бонусах"""
    with open(DAILY_BONUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Загружаем данные
ADMINS = load_admins()
APPLICATIONS = load_applications()
INVENTORY = load_inventory()
DAILY_BONUS_DATA = load_daily_bonus()

# Хранилище для связи пользователей и их обращений
user_appeals = {}
appeal_counter = 0

# ============== ПРОВЕРКА ПРАВ ==============
def get_admin_level(user_id):
    """Возвращает уровень админа (0 если не админ)"""
    admin_data = ADMINS.get(str(user_id))
    if admin_data:
        level = admin_data.get('level', 0)
        try:
            return int(level)
        except (ValueError, TypeError):
            return 0
    return 0

def is_admin(user_id, min_level=1):
    """Проверяет, является ли пользователь администратором"""
    level = get_admin_level(user_id)
    return level >= min_level

def is_owner(user_id):
    """Проверяет, является ли пользователь главным администратором"""
    return get_admin_level(user_id) == OWNER_LEVEL

def get_level_text(level):
    """Возвращает текст с уровнем админа"""
    try:
        level = int(level)
    except (ValueError, TypeError):
        level = 0
        
    if level == OWNER_LEVEL:
        return "👑 **Владелец** (Уровень 1000) - полный доступ"
    elif level >= 10:
        return f"👨‍💼 **Старший администратор** (Уровень {level}) - полный доступ к управлению"
    else:
        return f"👨‍💼 **Администратор** (Уровень {level}) - базовый доступ"

# ============== ТЕКСТЫ ПРАВИЛ ==============
rules_text = {
    "general": "📜 ОБЩИЕ ПРАВИЛА:\n\n1.1 Уважайте других игроков\n1.2 Запрещен читинг\n1.3 Запрещен гриферство\n1.4 Соблюдайте RP отыгровку",
    "chat": "💬 ЧАТ ПРАВИЛА:\n\n2.1 Не флудить\n2.2 Не капсить (писать ЗАГЛАВНЫМИ)\n2.3 Не оскорблять участников",
    "rp": "🎭 RP ПРАВИЛА:\n\n3.1 Обязательная отыгровка действий\n3.2 Запрещен DM (DeathMatch)\n3.3 Запрещен RK (RevengeKill)"
}

# ============== СОСТОЯНИЯ ДЛЯ ФОРМ ==============
class SupportForm(StatesGroup):
    waiting_for_issue = State()
    waiting_for_contact = State()

class ApplyForm(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_details = State()
    waiting_for_contact = State()

class AdminApplyForm(StatesGroup):
    waiting_for_age = State()
    waiting_for_experience = State()
    waiting_for_reason = State()

class AdminReplyForm(StatesGroup):
    waiting_for_reply = State()

class AddAdminForm(StatesGroup):
    waiting_for_id = State()
    waiting_for_name = State()
    waiting_for_level = State()

class ChangeAdminLevelForm(StatesGroup):
    waiting_for_level = State()

class AdminApplicationForm(StatesGroup):
    waiting_for_accept_text = State()

# ============== ГЛАВНОЕ МЕНЮ ==============
def get_main_keyboard(user_id=None):
    """Создает главную клавиатуру с кнопками как на картинке"""
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="▶️ Начать играть", callback_data="start_play")],
        [InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral")],
        [InlineKeyboardButton(text="🎁 Получение бонусов", callback_data="bonuses")],
        [InlineKeyboardButton(text="📋 Ежедневные задания", callback_data="daily_tasks")],
        [InlineKeyboardButton(text="🏆 Ежедневные награды", callback_data="daily_rewards")],
        [InlineKeyboardButton(text="📦 Хранилище предметов", callback_data="inventory")],
        [InlineKeyboardButton(text="📝 Подать заявку на админа", callback_data="apply_admin")],
    ]
    
    if user_id and is_admin(user_id):
        buttons.append([InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="admin_panel")])
    
    # Разбиваем на ряды по 2 кнопки
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

# ============== МЕНЮ ПРАВИЛ ==============
def get_rules_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📜 Общие", callback_data="rules_general")],
        [InlineKeyboardButton(text="💬 Чат", callback_data="rules_chat")],
        [InlineKeyboardButton(text="🎭 RP", callback_data="rules_rp")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ============== МЕНЮ ЗАЯВОК НА АДМИНА ==============
def get_admin_applications_keyboard():
    """Клавиатура для просмотра заявок на админа"""
    buttons = [
        [InlineKeyboardButton(text="📋 Список заявок", callback_data="admin_apps_list")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_application_action_keyboard(app_id):
    """Клавиатура для действий с заявкой"""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"app_accept_{app_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"app_reject_{app_id}")
        ],
        [InlineKeyboardButton(text="👤 Профиль", callback_data=f"app_profile_{app_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_apps_list")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ============== ИСПРАВЛЕННАЯ АДМИН-ПАНЕЛЬ ==============
def get_admin_keyboard(user_level):
    """Создает клавиатуру админ-панели в зависимости от уровня"""
    buttons = []
    
    # Кнопки, доступные всем админам
    buttons.append([InlineKeyboardButton(text="👥 Список админов", callback_data="admin_list")])
    buttons.append([InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")])
    
    # Кнопка заявок доступна админам с уровнем 10+
    if user_level >= 10:
        buttons.append([InlineKeyboardButton(text="📝 Заявки в админы", callback_data="admin_applications")])
    
    # Управление админами доступно с 10+ уровня
    if user_level >= 10:
        buttons.append([InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add")])
    
    # Кнопка назад для всех
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ============== ФУНКЦИИ ДЛЯ БОНУСОВ ==============
def get_user_inventory(user_id):
    """Получает инвентарь пользователя"""
    user_id_str = str(user_id)
    if user_id_str not in INVENTORY:
        INVENTORY[user_id_str] = {
            "items": [],
            "last_daily": None,
            "daily_streak": 0,
            "points": 0
        }
    return INVENTORY[user_id_str]

def add_item_to_inventory(user_id, item):
    """Добавляет предмет в инвентарь"""
    user_id_str = str(user_id)
    if user_id_str not in INVENTORY:
        INVENTORY[user_id_str] = {"items": [], "last_daily": None, "daily_streak": 0, "points": 0}
    INVENTORY[user_id_str]["items"].append({
        "name": item,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "used": False
    })
    save_inventory(INVENTORY)

def get_daily_reward(user_id):
    """Получает ежедневную награду"""
    user_id_str = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user_id_str not in DAILY_BONUS_DATA:
        DAILY_BONUS_DATA[user_id_str] = {
            "last_claim": None,
            "streak": 0,
            "total_claimed": 0
        }
    
    user_data = DAILY_BONUS_DATA[user_id_str]
    last_claim = user_data.get("last_claim")
    
    if last_claim == today:
        return {"success": False, "message": "Вы уже получили награду сегодня!"}
    
    if last_claim and (datetime.now() - datetime.strptime(last_claim, "%Y-%m-%d")).days == 1:
        user_data["streak"] += 1
    else:
        user_data["streak"] = 1
    
    user_data["last_claim"] = today
    user_data["total_claimed"] += 1
    
    rewards = [
        "🎫 Билет на розыгрыш",
        "💎 50 кристаллов",
        "💰 1000 монет",
        "🌟 Опыт x2 (1 час)",
        "🎁 Сундук с предметами",
        "🔑 Ключ от сундука"
    ]
    
    reward = random.choice(rewards)
    add_item_to_inventory(user_id, reward)
    
    save_daily_bonus(DAILY_BONUS_DATA)
    
    return {
        "success": True,
        "reward": reward,
        "streak": user_data["streak"],
        "total": user_data["total_claimed"]
    }

# ============== ОБРАБОТЧИК КОМАНДЫ /START ==============
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Отправляет приветствие с главным меню"""
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

# ============== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ ==============
@dp.callback_query(F.data == "stats")
async def show_stats(callback: CallbackQuery):
    """Показывает статистику"""
    user_id = callback.from_user.id
    user_inv = get_user_inventory(user_id)
    
    stats_text = f"""
📊 **Ваша статистика:**

👤 Профиль: {callback.from_user.full_name}
🆔 ID: {user_id}

📦 Предметов в хранилище: {len(user_inv['items'])}
⭐ Бонусные очки: {user_inv['points']}
📅 Дней в проекте: {user_inv['daily_streak']}

🔰 Рефералов: 0
    """
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============== ИСПРАВЛЕННЫЙ ОБРАБОТЧИК "НАЧАТЬ ИГРАТЬ" ==============
@dp.callback_query(F.data == "start_play")
async def start_play(callback: CallbackQuery):
    """Начать играть - без кнопки скачать, с новой ссылкой"""
    await callback.message.edit_text(
        "▶️ **Начать играть**\n\n"
        "Сервер: **VORTEX CRMP**\n"
        "IP: **play.vortexrp.online**\n\n"
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
    """Реферальная система"""
    ref_link = f"https://t.me/{(await bot.me()).username}?start=ref_{callback.from_user.id}"
    
    ref_text = f"""
👥 **Реферальная система**

Приглашай друзей и получай бонусы!

🔗 Твоя ссылка:
`{ref_link}`

🎁 Награды:
• 1 друг - 🎫 1 билет
• 3 друга - 💎 100 кристаллов
• 5 друзей - 👑 VIP на 3 дня
• 10 друзей - 🚗 Эксклюзивное авто

👥 Твои рефералы: 0
    """
    
    await callback.message.edit_text(
        ref_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "bonuses")
async def show_bonuses(callback: CallbackQuery):
    """Получение бонусов"""
    bonus_text = """
🎁 **Получение бонусов**

Доступные бонусы:

✅ **Ежедневный бонус** - заходи каждый день
✅ **Реферальный бонус** - приглашай друзей
✅ **Игровой бонус** - играй на сервере
✅ **Код дня** - активируй ежедневный код

👉 Используй /bonus для получения
    """
    
    await callback.message.edit_text(
        bonus_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "daily_tasks")
async def show_daily_tasks(callback: CallbackQuery):
    """Ежедневные задания"""
    tasks_text = """
📋 **Ежедневные задания**

🎯 **Задание 1:** Провести 1 час на сервере
   Награда: 🎫 1 билет

🎯 **Задание 2:** Заработать 10.000$ 
   Награда: 💰 5000$

🎯 **Задание 3:** Выполнить 5 миссий
   Награда: ⭐ 50 опыта

🎯 **Задание 4:** Пригласить друга
   Награда: 🎁 Сундук

⏳ До обновления: 12:34:56
    """
    
    await callback.message.edit_text(
        tasks_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "daily_rewards")
async def show_daily_rewards(callback: CallbackQuery):
    """Ежедневные награды"""
    user_id = callback.from_user.id
    reward_result = get_daily_reward(user_id)
    
    if reward_result["success"]:
        text = f"""
🏆 **Ежедневная награда получена!**

🎁 Ты получил: **{reward_result['reward']}**

🔥 Текущая серия: {reward_result['streak']} дней
📦 Предмет добавлен в хранилище

Заходи завтра для следующей награды!
        """
    else:
        text = f"""
🏆 **Ежедневные награды**

{reward_result['message']}

🔥 Твоя серия: {DAILY_BONUS_DATA.get(str(user_id), {}).get('streak', 0)} дней
📦 Всего получено: {DAILY_BONUS_DATA.get(str(user_id), {}).get('total_claimed', 0)} наград

Заходи каждый день и получай бонусы!
        """
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "inventory")
async def show_inventory(callback: CallbackQuery):
    """Хранилище предметов"""
    user_id = callback.from_user.id
    user_inv = get_user_inventory(user_id)
    
    if not user_inv['items']:
        items_text = "📦 В хранилище пока пусто\n\nПолучай предметы из ежедневных наград!"
    else:
        items_text = "📦 **Твои предметы:**\n\n"
        for i, item in enumerate(user_inv['items'], 1):
            status = "✅" if not item['used'] else "❌"
            items_text += f"{status} {i}. {item['name']} - {item['date']}\n"
    
    await callback.message.edit_text(
        items_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎁 Получить награду", callback_data="daily_rewards")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============== ИСПРАВЛЕННЫЙ ОБРАБОТЧИК ЗАЯВОК НА АДМИНА ==============
@dp.callback_query(F.data == "apply_admin")
async def apply_admin_start(callback: CallbackQuery, state: FSMContext):
    """Начать заявку на админа"""
    # Проверяем, не подавал ли уже заявку
    for app_id, app in APPLICATIONS.items():
        if app.get('user_id') == callback.from_user.id and app.get('status') == 'pending':
            await callback.answer("❌ Вы уже подали заявку! Ожидайте рассмотрения.", show_alert=True)
            return
    
    await callback.message.edit_text(
        "📝 **Заявка на администратора**\n\n"
        "Шаг 1 из 3\n\n"
        "Введите ваш возраст:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_main")]]
        ),
        parse_mode="Markdown"
    )
    await state.set_state(AdminApplyForm.waiting_for_age)
    await callback.answer()

@dp.message(AdminApplyForm.waiting_for_age)
async def process_admin_apply_age(message: types.Message, state: FSMContext):
    """Обрабатывает возраст"""
    await state.update_data(age=message.text)
    
    await message.answer(
        "📝 **Заявка на администратора**\n\n"
        "Шаг 2 из 3\n\n"
        "Расскажите о вашем опыте администрирования:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_main")]]
        ),
        parse_mode="Markdown"
    )
    await state.set_state(AdminApplyForm.waiting_for_experience)

@dp.message(AdminApplyForm.waiting_for_experience)
async def process_admin_apply_experience(message: types.Message, state: FSMContext):
    """Обрабатывает опыт"""
    await state.update_data(experience=message.text)
    
    await message.answer(
        "📝 **Заявка на администратора**\n\n"
        "Шаг 3 из 3\n\n"
        "Почему вы хотите стать администратором?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_main")]]
        ),
        parse_mode="Markdown"
    )
    await state.set_state(AdminApplyForm.waiting_for_reason)

@dp.message(AdminApplyForm.waiting_for_reason)
async def process_admin_apply_reason(message: types.Message, state: FSMContext):
    """Завершает заявку на админа"""
    data = await state.get_data()
    
    # Создаем заявку
    app_id = str(len(APPLICATIONS) + 1)
    APPLICATIONS[app_id] = {
        "id": app_id,
        "user_id": message.from_user.id,
        "user_name": message.from_user.full_name,
        "username": message.from_user.username,
        "age": data.get('age'),
        "experience": data.get('experience'),
        "reason": message.text,
        "status": "pending",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    save_applications(APPLICATIONS)
    
    # Уведомляем админов с уровнем 10+
    notified = False
    for admin_id in ADMINS.keys():
        if get_admin_level(int(admin_id)) >= 10:
            try:
                await bot.send_message(
                    int(admin_id),
                    f"📝 **Новая заявка в админы #{app_id}**\n\n"
                    f"👤 От: {message.from_user.full_name}\n"
                    f"🆔 ID: {message.from_user.id}\n"
                    f"📱 Username: @{message.from_user.username}\n"
                    f"📅 Возраст: {data.get('age')}\n"
                    f"📊 Опыт: {data.get('experience')}\n"
                    f"💭 Причина: {message.text}\n\n"
                    f"Используйте админ-панель для просмотра",
                    parse_mode="Markdown"
                )
                notified = True
            except Exception as e:
                logger.error(f"Ошибка при уведомлении админа {admin_id}: {e}")
    
    if not notified:
        logger.warning("Нет админов с уровнем 10+ для уведомления")
    
    await message.answer(
        "✅ **Заявка отправлена!**\n\n"
        "Администрация рассмотрит вашу заявку в ближайшее время.\n"
        "Статус заявки можно узнать в админ-панели (для админов).",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_main")]]
        )
    )
    await state.clear()

# ============== ОБРАБОТЧИКИ ДЛЯ АДМИНОВ (ЗАЯВКИ) ==============
@dp.callback_query(F.data == "admin_applications")
async def admin_applications_menu(callback: CallbackQuery):
    """Меню заявок в админы"""
    if not is_admin(callback.from_user.id, 10):
        await callback.answer("❌ Недостаточно прав!", show_alert=True)
        return
    
    pending = [app for app in APPLICATIONS.values() if app.get('status') == 'pending']
    
    text = f"📝 **Заявки в администраторы**\n\n"
    text += f"⏳ Ожидают рассмотрения: {len(pending)}\n"
    text += f"✅ Принято: {len([app for app in APPLICATIONS.values() if app.get('status') == 'accepted'])}\n"
    text += f"❌ Отклонено: {len([app for app in APPLICATIONS.values() if app.get('status') == 'rejected'])}"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_applications_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_apps_list")
async def admin_apps_list(callback: CallbackQuery):
    """Список заявок"""
    if not is_admin(callback.from_user.id, 10):
        await callback.answer("❌ Недостаточно прав!", show_alert=True)
        return
    
    pending = [app for app in APPLICATIONS.values() if app.get('status') == 'pending']
    
    if not pending:
        await callback.message.edit_text(
            "📝 Нет ожидающих заявок",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_applications")]]
            )
        )
        await callback.answer()
        return
    
    text = "📋 **Список заявок:**\n\n"
    buttons = []
    
    for app in pending[:10]:
        text += f"#{app['id']} - {app['user_name']} ({app['date']})\n"
        buttons.append([InlineKeyboardButton(
            text=f"📝 Заявка #{app['id']}", 
            callback_data=f"view_app_{app['id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_applications")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("view_app_"))
async def view_application(callback: CallbackQuery, state: FSMContext):
    """Просмотр заявки"""
    if not is_admin(callback.from_user.id, 10):
        await callback.answer("❌ Недостаточно прав!", show_alert=True)
        return
    
    app_id = callback.data.replace("view_app_", "")
    app = APPLICATIONS.get(app_id)
    
    if not app:
        await callback.answer("❌ Заявка не найдена!", show_alert=True)
        return
    
    text = f"""
📝 **Заявка #{app_id}**

👤 **Пользователь:** {app['user_name']}
🆔 **ID:** {app['user_id']}
📱 **Username:** @{app['username'] if app['username'] else 'нет'}

📅 **Возраст:** {app['age']}
📊 **Опыт:** {app['experience']}
💭 **Причина:** {app['reason']}

📆 **Дата:** {app['date']}
📌 **Статус:** {app['status']}
    """
    
    await callback.message.edit_text(
        text,
        reply_markup=get_application_action_keyboard(app_id),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("app_profile_"))
async def view_applicant_profile(callback: CallbackQuery):
    """Просмотр профиля пользователя"""
    if not is_admin(callback.from_user.id, 10):
        await callback.answer("❌ Недостаточно прав!", show_alert=True)
        return
    
    app_id = callback.data.replace("app_profile_", "")
    app = APPLICATIONS.get(app_id)
    
    if not app:
        await callback.answer("❌ Заявка не найдена!", show_alert=True)
        return
    
    user_id = app['user_id']
    user_inv = get_user_inventory(user_id)
    
    text = f"""
👤 **Профиль пользователя**

👤 Имя: {app['user_name']}
🆔 ID: {user_id}
📱 Username: @{app['username'] if app['username'] else 'нет'}

📦 Предметов: {len(user_inv['items'])}
🔥 Дней в проекте: {user_inv['daily_streak']}
📅 Всего наград: {DAILY_BONUS_DATA.get(str(user_id), {}).get('total_claimed', 0)}
    """
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"view_app_{app_id}")]
            ]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("app_accept_"))
async def accept_application(callback: CallbackQuery, state: FSMContext):
    """Принять заявку"""
    if not is_admin(callback.from_user.id, 10):
        await callback.answer("❌ Недостаточно прав!", show_alert=True)
        return
    
    app_id = callback.data.replace("app_accept_", "")
    app = APPLICATIONS.get(app_id)
    
    if not app:
        await callback.answer("❌ Заявка не найдена!", show_alert=True)
        return
    
    await state.update_data(app_id=app_id)
    
    await callback.message.edit_text(
        f"✏️ **Принятие заявки #{app_id}**\n\n"
        f"Введите текст, который будет отправлен пользователю при принятии:\n\n"
        f"(Например: Поздравляем! Ваша заявка принята. Ваш уровень: 1)",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data=f"view_app_{app_id}")]]
        ),
        parse_mode="Markdown"
    )
    await state.set_state(AdminApplicationForm.waiting_for_accept_text)
    await callback.answer()

@dp.message(AdminApplicationForm.waiting_for_accept_text)
async def process_accept_application(message: types.Message, state: FSMContext):
    """Обрабатывает текст принятия"""
    if not is_admin(message.from_user.id, 10):
        await message.answer("❌ Недостаточно прав!")
        await state.clear()
        return
    
    data = await state.get_data()
    app_id = data.get('app_id')
    app = APPLICATIONS.get(app_id)
    
    if not app:
        await message.answer("❌ Заявка не найдена!")
        await state.clear()
        return
    
    accept_text = message.text
    app['status'] = 'accepted'
    app['processed_by'] = message.from_user.full_name
    app['processed_date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_applications(APPLICATIONS)
    
    # Отправляем уведомление пользователю
    try:
        await bot.send_message(
            app['user_id'],
            f"✅ **Ваша заявка на администратора принята!**\n\n{accept_text}",
            parse_mode="Markdown"
        )
        logger.info(f"Уведомление отправлено пользователю {app['user_id']}")
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление пользователю {app['user_id']}: {e}")
    
    await message.answer(
        f"✅ **Заявка #{app_id} принята!**\n\nСообщение отправлено пользователю.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_panel")]]
        )
    )
    await state.clear()

@dp.callback_query(F.data.startswith("app_reject_"))
async def reject_application(callback: CallbackQuery):
    """Отклонить заявку"""
    if not is_admin(callback.from_user.id, 10):
        await callback.answer("❌ Недостаточно прав!", show_alert=True)
        return
    
    app_id = callback.data.replace("app_reject_", "")
    app = APPLICATIONS.get(app_id)
    
    if not app:
        await callback.answer("❌ Заявка не найдена!", show_alert=True)
        return
    
    app['status'] = 'rejected'
    app['processed_by'] = callback.from_user.full_name
    app['processed_date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_applications(APPLICATIONS)
    
    # Отправляем уведомление пользователю
    try:
        await bot.send_message(
            app['user_id'],
            "❌ **Ваша заявка на администратора отклонена.**\n\n"
            "Вы можете подать новую заявку через 7 дней.\n"
            "Спасибо за интерес к нашему проекту!",
            parse_mode="Markdown"
        )
        logger.info(f"Уведомление об отклонении отправлено пользователю {app['user_id']}")
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление пользователю {app['user_id']}: {e}")
    
    await callback.message.edit_text(
        f"❌ **Заявка #{app_id} отклонена**",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_panel")]]
        )
    )
    await callback.answer()

# ============== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ ==============
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "📌 **Главное меню:**",
        reply_markup=get_main_keyboard(callback.from_user.id),
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    """Админ-панель"""
    user_level = get_admin_level(callback.from_user.id)
    
    if user_level == 0:
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    level_text = get_level_text(user_level)
    
    await callback.message.edit_text(
        f"⚙️ **Админ-панель**\n\n{level_text}\n\nВыберите действие:",
        reply_markup=get_admin_keyboard(user_level),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============== ОБРАБОТЧИК КОМАНДЫ /ADMIN ==============
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Команда для управления админами"""
    user_level = get_admin_level(message.from_user.id)
    
    if user_level == 0:
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    
    level_text = get_level_text(user_level)
    
    await message.answer(
        f"⚙️ **Админ-панель**\n\n{level_text}\n\nВыберите действие:",
        reply_markup=get_admin_keyboard(user_level),
        parse_mode="Markdown"
    )

# ============== ОБРАБОТЧИК ДОБАВЛЕНИЯ АДМИНА ==============
@dp.callback_query(F.data == "admin_add")
async def admin_add_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление админа"""
    user_level = get_admin_level(callback.from_user.id)
    
    if user_level < 10:
        await callback.answer("❌ Только админы с уровнем 10+ могут добавлять новых!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "➕ **Добавление администратора**\n\nВведите Telegram ID пользователя, которого хотите сделать администратором:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_panel")]]
        ),
        parse_mode="Markdown"
    )
    await state.set_state(AddAdminForm.waiting_for_id)
    await callback.answer()

@dp.message(AddAdminForm.waiting_for_id)
async def process_add_admin_id(message: types.Message, state: FSMContext):
    """Получает ID нового админа"""
    user_level = get_admin_level(message.from_user.id)
    
    if user_level < 10:
        await message.answer("❌ У вас нет прав для этого действия.")
        await state.clear()
        return
    
    try:
        new_admin_id = int(message.text.strip())
        
        if str(new_admin_id) in ADMINS:
            await message.answer(
                "❌ Этот пользователь уже является администратором!",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_panel")]]
                )
            )
            await state.clear()
            return
        
        await state.update_data(new_admin_id=new_admin_id)
        max_level = user_level - 1
        
        await message.answer(
            f"✏️ **Введите имя/никнейм для нового администратора:**\n\n"
            f"⚠️ Максимальный уровень, который вы можете выдать: {max_level}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_panel")]]
            ),
            parse_mode="Markdown"
        )
        await state.set_state(AddAdminForm.waiting_for_name)
        
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректный ID (только цифры)!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_panel")]]
            )
        )

@dp.message(AddAdminForm.waiting_for_name)
async def process_add_admin_name(message: types.Message, state: FSMContext):
    """Получает имя нового админа"""
    user_level = get_admin_level(message.from_user.id)
    
    if user_level < 10:
        await message.answer("❌ У вас нет прав для этого действия.")
        await state.clear()
        return
    
    data = await state.get_data()
    new_admin_id = data.get('new_admin_id')
    admin_name = message.text.strip()
    
    await state.update_data(admin_name=admin_name)
    max_level = user_level - 1
    
    await message.answer(
        f"📊 **Введите уровень для нового администратора**\n\n"
        f"Имя: {admin_name}\n"
        f"ID: `{new_admin_id}`\n\n"
        f"Введите уровень (1-{max_level}):",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_panel")]]
        ),
        parse_mode="Markdown"
    )
    await state.set_state(AddAdminForm.waiting_for_level)

@dp.message(AddAdminForm.waiting_for_level)
async def process_add_admin_level(message: types.Message, state: FSMContext):
    """Получает уровень нового админа и добавляет его"""
    user_level = get_admin_level(message.from_user.id)
    
    if user_level < 10:
        await message.answer("❌ У вас нет прав для этого действия.")
        await state.clear()
        return
    
    try:
        new_level = int(message.text.strip())
        max_level = user_level - 1
        
        if new_level < 1 or new_level > max_level:
            await message.answer(
                f"❌ Уровень должен быть от 1 до {max_level}!",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_panel")]]
                )
            )
            return
        
        data = await state.get_data()
        new_admin_id = data.get('new_admin_id')
        admin_name = data.get('admin_name')
        
        ADMINS[str(new_admin_id)] = {
            "name": admin_name,
            "level": new_level,
            "added_by": message.from_user.full_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        save_admins(ADMINS)
        
        try:
            await bot.send_message(
                new_admin_id,
                f"✅ **Поздравляем!**\n\nВы были назначены администратором бота **VORTEX CRMP**!\n\n"
                f"📊 Ваш уровень: {new_level}\n"
                f"👤 Назначил: {message.from_user.full_name}\n\n"
                f"{'🔰 У вас полный доступ к управлению админами!' if new_level >= 10 else '📝 У вас базовые права администратора.'}",
                parse_mode="Markdown"
            )
        except:
            logger.warning(f"Не удалось отправить уведомление новому админу {new_admin_id}")
        
        await message.answer(
            f"✅ **Администратор успешно добавлен!**\n\n"
            f"ID: `{new_admin_id}`\n"
            f"Имя: {admin_name}\n"
            f"Уровень: {new_level}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_panel")]]
            ),
            parse_mode="Markdown"
        )
        
        logger.info(f"Новый администратор добавлен: {admin_name} ({new_admin_id}) с уровнем {new_level}")
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Пожалуйста, введите корректный уровень (только цифры)!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_panel")]]
            )
        )

# ============== ОБРАБОТЧИК СПИСКА АДМИНОВ ==============
@dp.callback_query(F.data == "admin_list")
async def show_admin_list(callback: CallbackQuery):
    """Показывает список админов"""
    user_level = get_admin_level(callback.from_user.id)
    
    if user_level == 0:
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    admin_list = "👥 **Список администраторов:**\n\n"
    for admin_id, admin_data in sorted(ADMINS.items(), key=lambda x: int(x[1].get('level', 0)), reverse=True):
        level = admin_data.get('level', 0)
        try:
            level = int(level)
        except:
            level = 0
            
        if level == OWNER_LEVEL:
            admin_list += f"👑 **{admin_data['name']}** (Владелец, ур. {level}) - `{admin_id}`\n"
        elif level >= 10:
            admin_list += f"🔰 **{admin_data['name']}** (Ст. админ, ур. {level}) - `{admin_id}`\n"
        else:
            admin_list += f"• {admin_data['name']} (ур. {level}) - `{admin_id}`\n"
    
    await callback.message.edit_text(
        admin_list,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============== ОБРАБОТЧИК СТАТИСТИКИ ==============
@dp.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery):
    """Показывает статистику для админов"""
    user_level = get_admin_level(callback.from_user.id)
    
    if user_level == 0:
        await callback.answer("❌ У вас нет доступа!", show_alert=True)
        return
    
    today_count = 0
    for appeal in user_appeals.values():
        if 'date' in appeal:
            try:
                appeal_date = datetime.strptime(appeal['date'].split()[0], '%Y-%m-%d')
                if (datetime.now() - appeal_date).days == 0:
                    today_count += 1
            except:
                pass
    
    stats = f"""
📊 **Статистика бота:**

👥 **Пользователи:**
• Всего обращений: {len(user_appeals)}

👨‍💼 **Администраторы:**
• Всего админов: {len(ADMINS)}
• Владелец (ур. 1000): 1
• Старшие админы (ур. 10+): {len([a for a in ADMINS.values() if int(a.get('level', 0)) >= 10 and int(a.get('level', 0)) < OWNER_LEVEL])}
• Обычные админы: {len([a for a in ADMINS.values() if int(a.get('level', 0)) < 10])}

📝 **За сегодня:**
• Обращений: {today_count}
    """
    
    await callback.message.edit_text(
        stats,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]]
        ),
        parse_mode="Markdown"
    )
    await callback.answer()

# ============== КОМАНДА /HELP ==============
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Показывает справку"""
    help_text = """
🆘 **Помощь по боту**

Доступные команды:
/start - Главное меню
/help - Эта справка
/rules - Правила сервера

👨‍💼 **Для администраторов:**
/admin - Админ-панель

По всем вопросам используйте кнопку "Связь с админом"
    """
    await message.answer(help_text, parse_mode="Markdown")

# ============== КОМАНДА /RULES ==============
@dp.message(Command("rules"))
async def cmd_rules(message: types.Message):
    """Быстрый доступ к правилам"""
    await message.answer(
        "📚 Выберите раздел правил:",
        reply_markup=get_rules_keyboard()
    )

# ============== ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ ==============
@dp.message(F.text)
async def handle_other_messages(message: types.Message):
    """Обрабатывает сообщения вне состояний"""
    
    if is_admin(message.from_user.id):
        if message.text.startswith('/'):
            return
        else:
            await message.answer(
                "👨‍💼 **Админ-панель:**\n\nИспользуйте кнопку ⚙️ в главном меню или команду /admin для управления.\n\nЧтобы ответить пользователю - нажмите кнопку 'Ответить' под обращением.",
                reply_markup=get_main_keyboard(message.from_user.id),
                parse_mode="Markdown"
            )
    else:
        await message.answer(
            "Используйте меню для навигации 👇",
            reply_markup=get_main_keyboard(message.from_user.id)
        )

# ============== ЗАПУСК БОТА ==============
async def main():
    print("🚀 Бот запущен и готов к работе!")
    print(f"👑 Владелец (уровень 1000) ID: {OWNER_ID}")
    print(f"👥 Администраторов в системе: {len(ADMINS)}")
    print("📊 Уровни админов:")
    print("   • 1000 - Владелец (полный доступ)")
    print("   • 10+ - Старшие админы (могут управлять админами)")
    print("   • 1-9 - Обычные админы (базовые права)")
    print("📝 Заявки на админов будут приходить админам с уровнем 10+")
    print("💬 Чтобы ответить пользователю - нажмите кнопку 'Ответить' под обращением")
    
    # Удаляем вебхук перед запуском
    await delete_webhook()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
