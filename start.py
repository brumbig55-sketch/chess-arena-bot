import asyncio
import threading
import uvicorn
from bot.config import settings

def run_webapp():
    uvicorn.run(
        "webapp.main_api:app",
        host="0.0.0.0",
        port=int(__import__("os").environ.get("PORT", 8000)),
        log_level="info",
    )

async def run_bot():
    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from bot.models.database import init_db
    from bot.handlers import start, game
    from bot.services.engine import engine_service

    await init_db()
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(game.router)

    try:
        await dp.start_polling(bot)
    finally:
        await engine_service.close()
        await bot.session.close()

if __name__ == "__main__":
    t = threading.Thread(target=run_webapp, daemon=True)
    t.start()
    asyncio.run(run_bot())
