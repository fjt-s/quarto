"""Flask web app: play Quarto against the GA-evolved minimax bot.

All game state lives in the signed session cookie, so the server itself is
stateless (no shared dict, works fine with multiple workers).
"""

from __future__ import annotations

import os
import secrets
from typing import Optional

from flask import Flask, jsonify, render_template, request, session

from ..board import Board
from ..game import IllegalMoveError, Phase, QuartoGame
from ..ai.evaluation import WEIGHT_SIZE
from ..ai.search import choose_action

DEFAULT_WEIGHTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "weights",
    "default.json",
)


def _load_default_weights():
    import json

    if os.path.exists(DEFAULT_WEIGHTS_PATH):
        with open(DEFAULT_WEIGHTS_PATH) as f:
            return json.load(f)["weights"]
    return [0.0] * WEIGHT_SIZE


BOT_WEIGHTS = _load_default_weights()
BOT_DEPTH = int(os.environ.get("QUARTO_BOT_DEPTH", "2"))


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("QUARTO_SECRET_KEY", secrets.token_hex(32))

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/new_game", methods=["POST"])
    def new_game():
        payload = request.get_json(silent=True) or {}
        human_player = 0 if payload.get("human_first", True) else 1
        squares_rule = bool(payload.get("squares_rule", False))

        game = QuartoGame(squares_rule=squares_rule)
        session["game"] = _serialize_game(game)
        session["human_player"] = human_player

        state = _game_state_response(game, human_player)
        state = _maybe_run_bot(game, human_player, state)
        return jsonify(state)

    @app.route("/api/state", methods=["GET"])
    def get_state():
        game = _load_game()
        if game is None:
            return jsonify({"error": "no active game"}), 404
        human_player = session.get("human_player", 0)
        return jsonify(_game_state_response(game, human_player))

    @app.route("/api/select", methods=["POST"])
    def select_piece():
        return _handle_human_action(lambda game, payload: game.select_piece(payload["piece"]))

    @app.route("/api/place", methods=["POST"])
    def place_piece():
        return _handle_human_action(lambda game, payload: game.place_piece(payload["row"], payload["col"]))

    def _handle_human_action(apply_fn):
        game = _load_game()
        if game is None:
            return jsonify({"error": "no active game"}), 404
        human_player = session.get("human_player", 0)
        if game.is_over:
            return jsonify({"error": "game is already over"}), 400
        if game.current_player != human_player:
            return jsonify({"error": "not your turn"}), 400

        payload = request.get_json(silent=True) or {}
        try:
            apply_fn(game, payload)
        except (IllegalMoveError, ValueError, KeyError, TypeError) as exc:
            return jsonify({"error": str(exc)}), 400

        session["game"] = _serialize_game(game)
        state = _game_state_response(game, human_player)
        state = _maybe_run_bot(game, human_player, state)
        return jsonify(state)

    return app


def _maybe_run_bot(game: QuartoGame, human_player: int, state: dict) -> dict:
    bot_player = 1 - human_player
    bot_actions = []
    while not game.is_over and game.current_player == bot_player:
        action = choose_action(game, BOT_WEIGHTS, depth=BOT_DEPTH)
        if game.phase == Phase.SELECT:
            game.select_piece(action)
            bot_actions.append({"type": "select", "piece": action})
        else:
            row, col = action
            game.place_piece(row, col)
            bot_actions.append({"type": "place", "row": row, "col": col})

    session["game"] = _serialize_game(game)
    state = _game_state_response(game, human_player)
    state["bot_actions"] = bot_actions
    return state


def _serialize_game(game: QuartoGame) -> dict:
    return {
        "grid": game.board.grid,
        "squares_rule": game.board.squares_rule,
        "available_pieces": game.available_pieces,
        "pending_piece": game.pending_piece,
        "current_player": game.current_player,
        "phase": game.phase.value,
        "winner": game.winner,
        "winning_line": list(game.winning_line) if game.winning_line else None,
        "is_draw": game.is_draw,
    }


def _load_game() -> Optional[QuartoGame]:
    data = session.get("game")
    if data is None:
        return None
    game = QuartoGame(squares_rule=data["squares_rule"])
    game.board = Board(squares_rule=data["squares_rule"])
    game.board.grid = data["grid"]
    game.available_pieces = data["available_pieces"]
    game.pending_piece = data["pending_piece"]
    game.current_player = data["current_player"]
    game.phase = Phase(data["phase"])
    game.winner = data["winner"]
    game.winning_line = [tuple(cell) for cell in data["winning_line"]] if data["winning_line"] else None
    game.is_draw = data["is_draw"]
    return game


def _game_state_response(game: QuartoGame, human_player: int) -> dict:
    return {
        "grid": game.board.grid,
        "squares_rule": game.board.squares_rule,
        "available_pieces": game.available_pieces,
        "pending_piece": game.pending_piece,
        "current_player": game.current_player,
        "human_player": human_player,
        "bot_player": 1 - human_player,
        "phase": game.phase.value,
        "winner": game.winner,
        "winning_line": game.winning_line,
        "is_draw": game.is_draw,
        "is_over": game.is_over,
    }


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", "5000")))
