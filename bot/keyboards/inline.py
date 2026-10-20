from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.config import settings

def main_menu_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Играть", web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}/play?user_id={user_id}"))],
        [InlineKeyboardButton(text="🤖 vs Бот", callback_data="play_bot"), InlineKeyboardButton(text="👥 vs Игрок", callback_data="play_pvp")],
        [InlineKeyboardButton(text="📊 Профиль", callback_data="profile"), InlineKeyboardButton(text="🏆 Рейтинг", callback_data="leaderboard")],
        [InlineKeyboardButton(text="🧩 Задачи", callback_data="puzzles"), InlineKeyboardButton(text="📈 Анализ", callback_data="analyze")],
        [InlineKeyboardButton(text="🎁 Сундуки", callback_data="chests"), InlineKeyboardButton(text="⭐ Premium", callback_data="premium")],
        [InlineKeyboardButton(text="🎮 Открыть Арену (WebApp)", web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}/?user_id={user_id}"))]
    ])

def bot_level_kb() -> InlineKeyboardMarkup:
    levels = [("🌱 Новичок (800)", 3), ("📘 Любитель (1200)", 6), ("⚔️ Средний (1600)", 10), ("🔥 Сильный (2000)", 14), ("👑 Гроссмейстер (2500+)", 18)]
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"bot_level:{lvl}")] for name, lvl in levels]
    buttons.append([InlineKeyboardButton(text="« Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def color_kb(level: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬜ Белыми", callback_data=f"start_bot:white:{level}"), InlineKeyboardButton(text="⬛ Чёрными", callback_data=f"start_bot:black:{level}")],
        [InlineKeyboardButton(text="🎲 Случайно", callback_data=f"start_bot:random:{level}")],
        [InlineKeyboardButton(text="« Назад", callback_data="play_bot")]
    ])

def game_actions_kb(game_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Открыть доску", web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}/game/{game_id}"))],
        [InlineKeyboardButton(text="🏳️ Сдаться", callback_data=f"resign:{game_id}"), InlineKeyboardButton(text="🤝 Ничья", callback_data=f"draw:{game_id}")]
    ])

def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Сменить тему", callback_data="change_theme")],
        [InlineKeyboardButton(text="« Назад", callback_data="main_menu")]
    ])

def after_game_kb(game_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Анализ партии", callback_data=f"analyze_game:{game_id}")],
        [InlineKeyboardButton(text="🔄 Ещё раз", callback_data="play_bot"), InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")]
    ])
