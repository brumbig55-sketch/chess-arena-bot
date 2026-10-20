from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy import select
from bot.models.database import async_session, User
from bot.keyboards.inline import main_menu_kb
from datetime import datetime, timezone

router = Router()

RANK_TITLES = [
    (800, "🌱 Novice"),
    (1000, "📘 Beginner"),
    (1200, "⚔️ Intermediate"),
    (1400, "🔥 Advanced"),
    (1600, "💎 Expert"),
    (1800, "🏆 Candidate Master"),
    (2000, "👑 Master"),
    (2200, "🌟 International Master"),
    (2400, "🔥 Grandmaster"),
    (2600, "Legendary"),
]

def get_rank(rating: float) -> str:
    title = "🌱 Novice"
    for threshold, name in RANK_TITLES:
        if rating >= threshold:
            title = name
    return title

@router.message(CommandStart())
async def cmd_start(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == message.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                display_name=message.from_user.first_name or "Player",
                rank_title=get_rank(1200)
            )
            session.add(user)
            await session.commit()
            welcome = (
                f"🎉 <b>Добро пожаловать в ChessArena!</b>\n\n"
                f"Привет, <b>{user.display_name}</b>!\n"
                f"Ты зарегистрирован. Начальный рейтинг: <b>1200</b>\n\n"
                f"⚔️ Играй против ботов и игроков\n"
                f"📊 Анализируй партии как на Chess.com\n"
                f"🏆 Сезонные рейтинги и награды\n"
                f"🎁 Сундуки, скины, Premium\n\n"
                f"Нажми <b>Играть</b> или открой WebApp-арену!"
            )
        else:
            user.last_active = datetime.now(timezone.utc)
            await session.commit()
            welcome = (
                f"👋 С возвращением, <b>{user.display_name}</b>!\n\n"
                f"📊 Classic: <b>{int(user.classic_rating)}</b> | Crown: <b>{int(user.crown_rating)}</b>\n"
                f"🏅 Ранг: {user.rank_title}\n"
                f"🎮 Партий: {user.games_played} | W/L/D: {user.wins}/{user.losses}/{user.draws}"
            )
    await message.answer(welcome, reply_markup=main_menu_kb(message.from_user.id), parse_mode="HTML")

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == callback.from_user.id))
        user = result.scalar_one_or_none()
    text = (
        f"🏠 <b>ChessArena</b>\n\n"
        f"Игрок: <b>{user.display_name if user else 'Player'}</b>\n"
        f"Рейтинг: <b>{int(user.classic_rating) if user else 1200}</b>\n\n"
        f"Выбери действие:"
    )
    await callback.message.edit_text(text, reply_markup=main_menu_kb(callback.from_user.id), parse_mode="HTML")
    await callback.answer()

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("🏠 Главное меню", reply_markup=main_menu_kb(message.from_user.id))
