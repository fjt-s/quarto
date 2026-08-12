"""Quarto game/turn state machine.

Turn structure (standard Quarto rules):
  1. Player A hands a piece to Player B (SELECT phase).
  2. Player B places that piece on the board (PLACE phase).
  3. If Player B just completed a winning line -> Player B wins.
     If the board is full with no winner -> draw.
  4. Otherwise Player B hands a piece to Player A, and so on.

The player who *places* a piece is the one who can win on that turn; the
player who *selects* a piece hands the opponent their weapon (or their
undoing), which is what makes Quarto interesting for adversarial search.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Tuple

from .board import Board

Cell = Tuple[int, int]


class Phase(Enum):
    SELECT = "select"  # current player must choose a piece for the opponent
    PLACE = "place"  # current player must place the given piece
    GAME_OVER = "game_over"


class IllegalMoveError(Exception):
    pass


class QuartoGame:
    def __init__(self, squares_rule: bool = False):
        self.board = Board(squares_rule=squares_rule)
        self.available_pieces: List[int] = list(range(16))
        self.pending_piece: Optional[int] = None
        self.current_player: int = 0  # 0 or 1; whoever must act next
        self.phase: Phase = Phase.SELECT
        self.winner: Optional[int] = None
        self.winning_line: Optional[Tuple[Cell, ...]] = None
        self.is_draw: bool = False
        self.last_move: Optional[dict] = None

    # -- derived state -----------------------------------------------
    @property
    def is_over(self) -> bool:
        return self.phase == Phase.GAME_OVER

    def legal_actions(self) -> List:
        if self.phase == Phase.SELECT:
            return list(self.available_pieces)
        if self.phase == Phase.PLACE:
            return self.board.empty_cells()
        return []

    def clone(self) -> "QuartoGame":
        new_game = QuartoGame(squares_rule=self.board.squares_rule)
        new_game.board = self.board.clone()
        new_game.available_pieces = list(self.available_pieces)
        new_game.pending_piece = self.pending_piece
        new_game.current_player = self.current_player
        new_game.phase = self.phase
        new_game.winner = self.winner
        new_game.winning_line = self.winning_line
        new_game.is_draw = self.is_draw
        return new_game

    # -- actions -------------------------------------------------------
    def select_piece(self, piece_id: int) -> None:
        if self.phase != Phase.SELECT:
            raise IllegalMoveError("not in select phase")
        if piece_id not in self.available_pieces:
            raise IllegalMoveError(f"piece {piece_id} is not available")
        self.available_pieces.remove(piece_id)
        self.pending_piece = piece_id
        self.current_player = 1 - self.current_player
        self.phase = Phase.PLACE
        self.last_move = {"type": "select", "piece": piece_id}

    def place_piece(self, row: int, col: int) -> None:
        if self.phase != Phase.PLACE:
            raise IllegalMoveError("not in place phase")
        if not self.board.is_empty(row, col):
            raise IllegalMoveError(f"cell ({row},{col}) is occupied")

        self.board.place(row, col, self.pending_piece)
        self.last_move = {
            "type": "place",
            "piece": self.pending_piece,
            "row": row,
            "col": col,
        }
        self.pending_piece = None

        line = self.board.winning_line()
        if line is not None:
            self.winner = self.current_player
            self.winning_line = line
            self.phase = Phase.GAME_OVER
            return

        if not self.available_pieces:
            # No pieces left to hand over: draw (whether or not a cell
            # remains open, since a piece is required to fill it).
            self.is_draw = True
            self.phase = Phase.GAME_OVER
            return

        if self.board.is_full():
            self.is_draw = True
            self.phase = Phase.GAME_OVER
            return

        self.phase = Phase.SELECT

    def apply(self, action) -> None:
        """Apply a select (int) or place ((row, col)) action generically."""
        if self.phase == Phase.SELECT:
            self.select_piece(action)
        elif self.phase == Phase.PLACE:
            row, col = action
            self.place_piece(row, col)
        else:
            raise IllegalMoveError("game is already over")

    def __repr__(self):
        return (
            f"QuartoGame(phase={self.phase.value}, current_player={self.current_player}, "
            f"pending_piece={self.pending_piece}, winner={self.winner}, draw={self.is_draw})\n"
            f"{self.board!r}"
        )
