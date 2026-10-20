import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.config import settings
from bot.models.database import init_db
from bot.handlers import start, game
from bot.services.engine import engine_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    await init_db()
    logger.info("Database initialized")
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(game.router)
    logger.info("Starting ChessArena Bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await engine_service.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
