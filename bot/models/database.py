from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, BigInteger
from datetime import datetime, timezone
from bot.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    display_name: Mapped[str] = mapped_column(String(64), default="Player")
    classic_rating: Mapped[float] = mapped_column(Float, default=1200.0)
    classic_rd: Mapped[float] = mapped_column(Float, default=350.0)
    crown_rating: Mapped[float] = mapped_column(Float, default=0.0)
    crown_points: Mapped[int] = mapped_column(Integer, default=0)
    games_played: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analysis_used_today: Mapped[int] = mapped_column(Integer, default=0)
    last_analysis_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    avatar: Mapped[str] = mapped_column(String(64), default="default")
    board_theme: Mapped[str] = mapped_column(String(32), default="classic")
    piece_set: Mapped[str] = mapped_column(String(32), default="cburnett")
    rank_title: Mapped[str] = mapped_column(String(32), default="Novice")
    coins: Mapped[int] = mapped_column(Integer, default=100)
    chests_opened: Mapped[int] = mapped_column(Integer, default=0)
    inventory: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_active: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    games = relationship("Game", back_populates="user", foreign_keys="Game.user_id")

class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    opponent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    opponent_name: Mapped[str] = mapped_column(String(64), default="Stockfish")
    pgn: Mapped[str] = mapped_column(Text, default="")
    fen: Mapped[str] = mapped_column(String(128), default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    result: Mapped[str | None] = mapped_column(String(16), nullable=True)
    winner: Mapped[str | None] = mapped_column(String(16), nullable=True)
    time_control: Mapped[str] = mapped_column(String(16), default="5+0")
    player_color: Mapped[str] = mapped_column(String(8), default="white")
    bot_level: Mapped[int] = mapped_column(Integer, default=5)
    accuracy_white: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_black: Mapped[float | None] = mapped_column(Float, nullable=True)
    analysis_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_rated: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user = relationship("User", back_populates="games", foreign_keys=[user_id])

class Season(Base):
    __tablename__ = "seasons"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    number: Mapped[int] = mapped_column(Integer, unique=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
