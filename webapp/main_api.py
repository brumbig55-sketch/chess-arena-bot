from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from bot.models.database import async_session, User, Game, init_db
from bot.services.engine import engine_service
from bot.config import settings
import chess
from datetime import datetime, timezone
import random

app = FastAPI(title="ChessArena WebApp", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

try:
    app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
except Exception:
    pass
templates = Jinja2Templates(directory="webapp/templates")

class MoveRequest(BaseModel):
    game_id: int
    move: str
    user_id: int

class CreateGameRequest(BaseModel):
    user_id: int
    color: str = "white"
    bot_level: int = 10
    time_control: str = "5+0"

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user_id: Optional[int] = None):
    return templates.TemplateResponse("index.html", {"request": request, "user_id": user_id or 0, "webapp_url": settings.WEBAPP_URL})

@app.get("/play", response_class=HTMLResponse)
async def play_page(request: Request, user_id: Optional[int] = None):
    return templates.TemplateResponse("play.html", {"request": request, "user_id": user_id or 0})

@app.get("/game/{game_id}", response_class=HTMLResponse)
async def game_page(request: Request, game_id: int, user_id: Optional[int] = None):
    return templates.TemplateResponse("game.html", {"request": request, "game_id": game_id, "user_id": user_id or 0})

@app.get("/api/user/{user_id}")
async def get_user(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(404, "User not found")
        return {"id": user.id, "display_name": user.display_name, "classic_rating": int(user.classic_rating),
                "crown_rating": int(user.crown_rating), "rank_title": user.rank_title, "games_played": user.games_played,
                "wins": user.wins, "losses": user.losses, "draws": user.draws, "is_premium": user.is_premium,
                "board_theme": user.board_theme, "piece_set": user.piece_set, "coins": user.coins}

@app.post("/api/game/create")
async def create_game(req: CreateGameRequest):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == req.user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=req.user_id, display_name=f"Player{req.user_id}")
            session.add(user)
            await session.commit()
        color = req.color if req.color != "random" else random.choice(["white", "black"])
        game = Game(user_id=req.user_id, opponent_name=f"Stockfish Lv{req.bot_level}", player_color=color,
                    bot_level=req.bot_level, time_control=req.time_control, status="active",
                    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        session.add(game)
        await session.commit()
        await session.refresh(game)
        bot_move = None
        bot_san = None
        if color == "black":
            board = chess.Board(game.fen)
            bot_uci = await engine_service.get_best_move(board.fen(), skill_level=req.bot_level, time_limit=0.5)
            if bot_uci:
                move = chess.Move.from_uci(bot_uci)
                bot_san = board.san(move)
                board.push(move)
                game.fen = board.fen()
                game.pgn = f"1. {bot_san}"
                bot_move = bot_uci
                await session.commit()
        return {"game_id": game.id, "fen": game.fen, "player_color": game.player_color,
                "bot_level": game.bot_level, "status": game.status, "bot_first_move": bot_move, "bot_first_san": bot_san}

@app.get("/api/game/{game_id}")
async def get_game(game_id: int):
    async with async_session() as session:
        result = await session.execute(select(Game).where(Game.id == game_id))
        game = result.scalar_one_or_none()
        if not game:
            raise HTTPException(404, "Game not found")
        board = chess.Board(game.fen)
        return {"id": game.id, "fen": game.fen, "pgn": game.pgn, "player_color": game.player_color,
                "bot_level": game.bot_level, "opponent_name": game.opponent_name, "status": game.status,
                "result": game.result, "turn": "white" if board.turn == chess.WHITE else "black",
                "is_check": board.is_check(), "is_game_over": board.is_game_over(),
                "legal_moves": [m.uci() for m in board.legal_moves]}

@app.post("/api/game/move")
async def make_move(req: MoveRequest):
    if req.move == "resign":
        async with async_session() as session:
            result = await session.execute(select(Game).where(Game.id == req.game_id))
            game = result.scalar_one_or_none()
            if game and game.status == "active":
                game.status = "finished"
                game.result = "0-1" if game.player_color == "white" else "1-0"
                game.finished_at = datetime.now(timezone.utc)
                await session.commit()
            return {"ok": True, "is_game_over": True, "result": game.result if game else "0-1"}
    async with async_session() as session:
        result = await session.execute(select(Game).where(Game.id == req.game_id))
        game = result.scalar_one_or_none()
        if not game:
            raise HTTPException(404, "Game not found")
        if game.status != "active":
            raise HTTPException(400, "Game is finished")
        if game.user_id != req.user_id:
            raise HTTPException(403, "Not your game")
        board = chess.Board(game.fen)
        player_is_white = game.player_color == "white"
        try:
            move = chess.Move.from_uci(req.move)
            if move not in board.legal_moves:
                raise HTTPException(400, "Illegal move")
        except Exception:
            raise HTTPException(400, "Invalid move")
        san = board.san(move)
        board.push(move)
        game.fen = board.fen()
        response = {"ok": True, "fen": game.fen, "san": san, "is_game_over": False, "result": None, "bot_move": None, "bot_san": None}
        if board.is_game_over():
            game.status = "finished"
            game.finished_at = datetime.now(timezone.utc)
            if board.is_checkmate():
                game.result = "1-0" if board.turn == chess.BLACK else "0-1"
                game.winner = "white" if board.turn == chess.BLACK else "black"
            else:
                game.result = "1/2-1/2"
                game.winner = "draw"
            user_res = await session.execute(select(User).where(User.id == game.user_id))
            user = user_res.scalar_one()
            user.games_played += 1
            if game.winner == "draw":
                user.draws += 1
                user.classic_rating += 5
            elif (game.winner == "white" and player_is_white) or (game.winner == "black" and not player_is_white):
                user.wins += 1
                user.classic_rating += 20
                user.crown_points += 10
            else:
                user.losses += 1
                user.classic_rating = max(100, user.classic_rating - 15)
            response["is_game_over"] = True
            response["result"] = game.result
            await session.commit()
            return response
        bot_is_white = game.player_color == "black"
        if (board.turn == chess.WHITE) == bot_is_white:
            bot_uci = await engine_service.get_best_move(board.fen(), skill_level=game.bot_level, time_limit=0.8)
            if bot_uci:
                bot_move = chess.Move.from_uci(bot_uci)
                bot_san = board.san(bot_move)
                board.push(bot_move)
                game.fen = board.fen()
                response["bot_move"] = bot_uci
                response["bot_san"] = bot_san
                response["fen"] = game.fen
                if board.is_game_over():
                    game.status = "finished"
                    game.finished_at = datetime.now(timezone.utc)
                    if board.is_checkmate():
                        game.result = "1-0" if board.turn == chess.BLACK else "0-1"
                        game.winner = "white" if board.turn == chess.BLACK else "black"
                    else:
                        game.result = "1/2-1/2"
                        game.winner = "draw"
                    user_res = await session.execute(select(User).where(User.id == game.user_id))
                    user = user_res.scalar_one()
                    user.games_played += 1
                    if game.winner == "draw":
                        user.draws += 1
                        user.classic_rating += 5
                    elif (game.winner == "white" and player_is_white) or (game.winner == "black" and not player_is_white):
                        user.wins += 1
                        user.classic_rating += 20
                    else:
                        user.losses += 1
                        user.classic_rating = max(100, user.classic_rating - 15)
                    response["is_game_over"] = True
                    response["result"] = game.result
        game.pgn = (game.pgn or "") + f" {san}"
        if response.get("bot_san"):
            game.pgn += f" {response['bot_san']}"
        await session.commit()
        return response

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ChessArena"}
