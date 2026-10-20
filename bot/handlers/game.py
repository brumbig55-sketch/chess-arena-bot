from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from bot.models.database import async_session, User, Game
from bot.keyboards.inline import bot_level_kb, color_kb, game_actions_kb, after_game_kb, main_menu_kb, profile_kb
from datetime import datetime, timezone
import random

router = Router()

@router.callback_query(F.data == "play_bot")
async def cb_play_bot(callback: CallbackQuery):
    await callback.message.edit_text("🤖 <b>Игра против бота</b>\n\nВыбери уровень сложности:", reply_markup=bot_level_kb(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("bot_level:"))
async def cb_bot_level(callback: CallbackQuery):
    level = int(callback.data.split(":")[1])
    names = {3: "Новичок", 6: "Любитель", 10: "Средний", 14: "Сильный", 18: "Гроссмейстер"}
    await callback.message.edit_text(f"Выбран уровень: <b>{names.get(level, level)}</b>\n\nВыбери цвет:", reply_markup=color_kb(level), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("start_bot:"))
async def cb_start_bot(callback: CallbackQuery):
    parts = callback.data.split(":")
    color = parts[1]
    level = int(parts[2])
    if color == "random":
        color = random.choice(["white", "black"])
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == callback.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            await callback.answer("Сначала /start", show_alert=True)
            return
        game = Game(user_id=user.id, opponent_name=f"Stockfish Lv{level}", player_color=color, bot_level=level, time_control="5+0", status="active")
        session.add(game)
        await session.commit()
        await session.refresh(game)
        game_id = game.id
    color_emoji = "⬜" if color == "white" else "⬛"
    text = f"⚔️ <b>Игра началась!</b>\n\nТы играешь {color_emoji} <b>{'белыми' if color == 'white' else 'чёрными'}</b>\nПротив: <b>Stockfish Lv{level}</b>\nКонтроль: 5+0\n\nОткрой доску в WebApp и делай ходы!"
    await callback.message.edit_text(text, reply_markup=game_actions_kb(game_id), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("resign:"))
async def cb_resign(callback: CallbackQuery):
    game_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        result = await session.execute(select(Game).where(Game.id == game_id))
        game = result.scalar_one_or_none()
        if not game or game.user_id != callback.from_user.id:
            await callback.answer("Игра не найдена", show_alert=True)
            return
        if game.status != "active":
            await callback.answer("Игра уже завершена", show_alert=True)
            return
        game.status = "finished"
        game.result = "0-1" if game.player_color == "white" else "1-0"
        game.winner = "black" if game.player_color == "white" else "white"
        game.finished_at = datetime.now(timezone.utc)
        user_result = await session.execute(select(User).where(User.id == game.user_id))
        user = user_result.scalar_one()
        user.games_played += 1
        user.losses += 1
        user.classic_rating = max(100, user.classic_rating - 15)
        await session.commit()
    await callback.message.edit_text(f"🏳️ Ты сдался.\n\nРезультат: <b>{game.result}</b>\nРейтинг: {int(user.classic_rating)}", reply_markup=after_game_kb(game_id), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "play_pvp")
async def cb_play_pvp(callback: CallbackQuery):
    await callback.message.edit_text("👥 <b>Игра против игрока</b>\n\nМатчмейкинг в разработке.\nПока используй WebApp или играй против бота.", reply_markup=main_menu_kb(callback.from_user.id), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "profile")
async def cb_profile(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == callback.from_user.id))
        user = result.scalar_one_or_none()
    if not user:
        await callback.answer("Сначала /start", show_alert=True)
        return
    winrate = round(user.wins / user.games_played * 100, 1) if user.games_played > 0 else 0
    text = (f"👤 <b>Профиль</b>\n\nИмя: <b>{user.display_name}</b>\nUsername: @{user.username or '—'}\n\n"
            f"📊 <b>Рейтинги</b>\nClassic: <b>{int(user.classic_rating)}</b>\nCrown: <b>{int(user.crown_rating)}</b>\nРанг: {user.rank_title}\n\n"
            f"🎮 <b>Статистика</b>\nПартий: {user.games_played}\nПобеды: {user.wins} | Поражения: {user.losses} | Ничьи: {user.draws}\nВинрейт: {winrate}%\n\n"
            f"💰 Монеты: {user.coins}\n⭐ Premium: {'Да' if user.is_premium else 'Нет'}")
    await callback.message.edit_text(text, reply_markup=profile_kb(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "leaderboard")
async def cb_leaderboard(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).order_by(User.classic_rating.desc()).limit(10))
        top = result.scalars().all()
    text = "🏆 <b>Топ-10 Classic Rating</b>\n\n"
    medals = ["🥇", "🥈", "🥉"] + ["▫️"] * 7
    for i, u in enumerate(top):
        text += f"{medals[i]} <b>{u.display_name}</b> — {int(u.classic_rating)}\n"
    if not top:
        text += "Пока никого нет. Будь первым!"
    await callback.message.edit_text(text, reply_markup=main_menu_kb(callback.from_user.id), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "puzzles")
async def cb_puzzles(callback: CallbackQuery):
    await callback.message.edit_text("🧩 <b>Шахматные задачи</b>\n\nDaily Puzzle и Puzzle Rush скоро!", reply_markup=main_menu_kb(callback.from_user.id), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "chests")
async def cb_chests(callback: CallbackQuery):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == callback.from_user.id))
        user = result.scalar_one_or_none()
    text = f"🎁 <b>Сундуки</b>\n\nМонеты: <b>{user.coins if user else 0}</b>\nОткрыто сундуков: {user.chests_opened if user else 0}\n\nСкоро: ежедневные сундуки и скины!"
    await callback.message.edit_text(text, reply_markup=main_menu_kb(callback.from_user.id), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "premium")
async def cb_premium(callback: CallbackQuery):
    text = "⭐ <b>ChessArena Premium</b>\n\n• Бесконечный анализ\n• Полная статистика\n• Эксклюзивные темы\n• Приоритет в матчмейкинге\n• Доп. сундуки\n\nОплата через Telegram Stars — скоро!"
    await callback.message.edit_text(text, reply_markup=main_menu_kb(callback.from_user.id), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "analyze")
async def cb_analyze_menu(callback: CallbackQuery):
    await callback.message.edit_text("📈 <b>Анализ партий</b>\n\nОтправь PGN текстом или выбери завершённую партию.\nБесплатно: 3 анализа в день.", reply_markup=main_menu_kb(callback.from_user.id), parse_mode="HTML")
    await callback.answer()
