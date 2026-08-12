"""4x4 Quarto board and win detection."""

from __future__ import annotations

from typing import List, Optional, Tuple

from .piece import common_mask

SIZE = 4

Cell = Tuple[int, int]


def _rows() -> List[List[Cell]]:
    return [[(r, c) for c in range(SIZE)] for r in range(SIZE)]


def _cols() -> List[List[Cell]]:
    return [[(r, c) for r in range(SIZE)] for c in range(SIZE)]


def _diagonals() -> List[List[Cell]]:
    return [
        [(i, i) for i in range(SIZE)],
        [(i, SIZE - 1 - i) for i in range(SIZE)],
    ]


def _squares() -> List[List[Cell]]:
    """The four 2x2 sub-squares (a common optional Quarto win condition)."""
    return [
        [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
        for r in range(SIZE - 1)
        for c in range(SIZE - 1)
    ]


LINES: Tuple[Tuple[Cell, ...], ...] = tuple(
    tuple(line) for line in (*_rows(), *_cols(), *_diagonals())
)

SQUARE_LINES: Tuple[Tuple[Cell, ...], ...] = tuple(tuple(sq) for sq in _squares())


class Board:
    """Mutable 4x4 grid of pieces (ints) or None for empty cells."""

    def __init__(self, squares_rule: bool = False):
        self.grid: List[List[Optional[int]]] = [[None] * SIZE for _ in range(SIZE)]
        self.squares_rule = squares_rule

    def clone(self) -> "Board":
        new_board = Board(squares_rule=self.squares_rule)
        new_board.grid = [row[:] for row in self.grid]
        return new_board

    def is_empty(self, row: int, col: int) -> bool:
        return self.grid[row][col] is None

    def place(self, row: int, col: int, piece_id: int) -> None:
        if not (0 <= row < SIZE and 0 <= col < SIZE):
            raise ValueError(f"cell ({row},{col}) out of bounds")
        if self.grid[row][col] is not None:
            raise ValueError(f"cell ({row},{col}) is already occupied")
        self.grid[row][col] = piece_id

    def empty_cells(self) -> List[Cell]:
        return [
            (r, c)
            for r in range(SIZE)
            for c in range(SIZE)
            if self.grid[r][c] is None
        ]

    def is_full(self) -> bool:
        return all(self.grid[r][c] is not None for r in range(SIZE) for c in range(SIZE))

    def _line_pieces(self, line: Tuple[Cell, ...]) -> List[int]:
        return [self.grid[r][c] for r, c in line if self.grid[r][c] is not None]

    def line_status(self, line: Tuple[Cell, ...]) -> Tuple[int, int]:
        """Return (filled_count, alive_attribute_count) for a line."""
        pieces = self._line_pieces(line)
        mask = common_mask(pieces)
        return len(pieces), bin(mask).count("1")

    def all_lines(self) -> Tuple[Tuple[Cell, ...], ...]:
        return LINES + SQUARE_LINES if self.squares_rule else LINES

    def winning_line(self) -> Optional[Tuple[Cell, ...]]:
        """Return the first fully-filled line that shares an attribute, if any."""
        for line in self.all_lines():
            pieces = self._line_pieces(line)
            if len(pieces) == SIZE and common_mask(pieces) != 0:
                return line
        return None

    def has_winner(self) -> bool:
        return self.winning_line() is not None

    def __repr__(self):
        rows = []
        for r in range(SIZE):
            rows.append(
                " ".join(
                    f"{self.grid[r][c]:2d}" if self.grid[r][c] is not None else " ."
                    for c in range(SIZE)
                )
            )
        return "\n".join(rows)
