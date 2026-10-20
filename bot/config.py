from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    BOT_TOKEN: str = "YOUR_BOT_TOKEN"
    WEBAPP_URL: str = "http://localhost:8000"
    SECRET_KEY: str = "change_me_super_secret_key_32chars!!"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/chess_arena.db"
    STOCKFISH_PATH: str = "/usr/games/stockfish"
    ADMIN_IDS: List[int] = []
    DEFAULT_TIME_CONTROL: str = "5+0"
    MAX_ANALYSIS_FREE: int = 3
    SEASON_DAYS: int = 7
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
