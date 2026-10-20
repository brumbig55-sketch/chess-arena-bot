import chess
import chess.engine
import chess.pgn
from typing import Optional, Dict, List
from bot.config import settings
import io
import asyncio

class ChessEngineService:
    def __init__(self):
        self.engine_path = settings.STOCKFISH_PATH
        self._engine: Optional[chess.engine.SimpleEngine] = None

    async def get_engine(self) -> chess.engine.SimpleEngine:
        if self._engine is None:
            try:
                self._engine = await asyncio.to_thread(
                    chess.engine.SimpleEngine.popen_uci, self.engine_path
                )
            except Exception as e:
                for path in ["/usr/bin/stockfish", "/usr/local/bin/stockfish", "stockfish", "/usr/games/stockfish"]:
                    try:
                        self._engine = await asyncio.to_thread(
                            chess.engine.SimpleEngine.popen_uci, path
                        )
                        break
                    except Exception:
                        continue
                if self._engine is None:
                    raise RuntimeError(f"Stockfish not found: {e}")
        return self._engine

    async def close(self):
        if self._engine:
            await asyncio.to_thread(self._engine.quit)
            self._engine = None

    async def get_best_move(self, fen: str, skill_level: int = 10, time_limit: float = 0.5) -> Optional[str]:
        engine = await self.get_engine()
        board = chess.Board(fen)
        skill = max(0, min(20, skill_level))
        limit = chess.engine.Limit(time=time_limit)
        await asyncio.to_thread(engine.configure, {"Skill Level": skill})
        result = await asyncio.to_thread(engine.play, board, limit)
        if result.move:
            return result.move.uci()
        return None

    async def analyze_position(self, fen: str, depth: int = 18) -> Dict:
        engine = await self.get_engine()
        board = chess.Board(fen)
        info = await asyncio.to_thread(engine.analyse, board, chess.engine.Limit(depth=depth))
        score = info.get("score")
        pv = info.get("pv", [])
        return {
            "score": str(score.white()) if score else None,
            "best_move": pv[0].uci() if pv else None,
            "pv": [m.uci() for m in pv[:5]],
            "depth": info.get("depth"),
        }

    async def analyze_game(self, pgn_str: str, depth: int = 16) -> Dict:
        engine = await self.get_engine()
        pgn = chess.pgn.read_game(io.StringIO(pgn_str))
        if not pgn:
            return {"error": "Invalid PGN"}
        board = pgn.board()
        moves_analysis = []
        white_cpl = []
        black_cpl = []
        node = pgn
        move_number = 0
        while node.variations:
            next_node = node.variation(0)
            move = next_node.move
            move_number += 1
            info_before = await asyncio.to_thread(engine.analyse, board, chess.engine.Limit(depth=depth))
            best_score_before = info_before["score"].white().score(mate_score=10000) if info_before.get("score") else 0
            best_move = info_before.get("pv", [None])[0]
            san = board.san(move)
            board.push(move)
            info_after = await asyncio.to_thread(engine.analyse, board, chess.engine.Limit(depth=depth))
            score_after = info_after["score"].white().score(mate_score=10000) if info_after.get("score") else 0
            if board.turn == chess.BLACK:
                cpl = max(0, best_score_before - score_after)
                white_cpl.append(cpl)
                side = "white"
            else:
                cpl = max(0, score_after - best_score_before)
                black_cpl.append(cpl)
                side = "black"
            classification = self._classify_move(cpl, best_move == move if best_move else False, board.is_check())
            moves_analysis.append({
                "move_number": (move_number + 1) // 2,
                "san": san,
                "uci": move.uci(),
                "side": side,
                "cpl": cpl,
                "classification": classification,
                "best_move": best_move.uci() if best_move else None,
                "score": score_after,
            })
            node = next_node
        def calc_accuracy(cpls: List[float]) -> float:
            if not cpls:
                return 100.0
            avg_cpl = sum(cpls) / len(cpls)
            return round(max(0, min(100, 100 - avg_cpl * 0.8)), 1)
        return {
            "moves": moves_analysis,
            "accuracy_white": calc_accuracy(white_cpl),
            "accuracy_black": calc_accuracy(black_cpl),
            "white_cpl_avg": round(sum(white_cpl) / len(white_cpl), 1) if white_cpl else 0,
            "black_cpl_avg": round(sum(black_cpl) / len(black_cpl), 1) if black_cpl else 0,
            "brilliant_count": sum(1 for m in moves_analysis if m["classification"] == "brilliant"),
            "great_count": sum(1 for m in moves_analysis if m["classification"] == "great"),
            "blunder_count": sum(1 for m in moves_analysis if m["classification"] == "blunder"),
            "mistake_count": sum(1 for m in moves_analysis if m["classification"] == "mistake"),
        }

    def _classify_move(self, cpl: float, is_best: bool, is_check: bool) -> str:
        if is_best and cpl < 10:
            return "best" if cpl == 0 else "excellent"
        if cpl == 0 or (is_best and cpl < 20):
            return "best"
        if cpl < 20:
            return "good"
        if cpl < 50:
            return "inaccuracy"
        if cpl < 100:
            return "mistake"
        if is_best and is_check and cpl < 5:
            return "brilliant"
        return "blunder" if cpl >= 100 else "mistake"

engine_service = ChessEngineService()
