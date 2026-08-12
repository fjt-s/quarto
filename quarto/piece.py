"""Quarto piece representation.

Each piece has four binary attributes, encoded as bits of an int 0-15:
  bit 0 (1): height  -> 0 = short,  1 = tall
  bit 1 (2): color   -> 0 = light,  1 = dark
  bit 2 (4): shape   -> 0 = square, 1 = round
  bit 3 (8): fill    -> 0 = hollow, 1 = solid

There are exactly 16 pieces, one for every combination of attributes.
"""

from __future__ import annotations

HEIGHT_BIT = 0
COLOR_BIT = 1
SHAPE_BIT = 2
FILL_BIT = 3

ATTRIBUTE_BITS = (HEIGHT_BIT, COLOR_BIT, SHAPE_BIT, FILL_BIT)

ATTRIBUTE_LABELS = {
    HEIGHT_BIT: ("short", "tall"),
    COLOR_BIT: ("light", "dark"),
    SHAPE_BIT: ("square", "round"),
    FILL_BIT: ("hollow", "solid"),
}

ALL_PIECES = tuple(range(16))


class Piece:
    """Thin helper around a piece id (0-15) for readable attribute access."""

    __slots__ = ("id",)

    def __init__(self, piece_id: int):
        if not 0 <= piece_id <= 15:
            raise ValueError(f"piece id must be in 0..15, got {piece_id}")
        self.id = piece_id

    def has_attribute(self, bit: int) -> bool:
        return bool(self.id & (1 << bit))

    @property
    def is_tall(self) -> bool:
        return self.has_attribute(HEIGHT_BIT)

    @property
    def is_dark(self) -> bool:
        return self.has_attribute(COLOR_BIT)

    @property
    def is_round(self) -> bool:
        return self.has_attribute(SHAPE_BIT)

    @property
    def is_solid(self) -> bool:
        return self.has_attribute(FILL_BIT)

    def describe(self) -> str:
        return "-".join(
            ATTRIBUTE_LABELS[bit][self.has_attribute(bit)] for bit in ATTRIBUTE_BITS
        )

    def __eq__(self, other):
        if isinstance(other, Piece):
            return self.id == other.id
        return self.id == other

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f"Piece({self.id}:{self.describe()})"


def common_mask(piece_ids) -> int:
    """Return the bitmask of attributes shared by every piece in piece_ids.

    A bit is set in the result if all given pieces agree on that attribute
    (all 1 or all 0). Returns 0xF (all attributes shared) for an empty input,
    matching the identity element for AND/OR reduction.
    """
    piece_ids = list(piece_ids)
    if not piece_ids:
        return 0xF
    and_bits = 0xF
    or_bits = 0x0
    for pid in piece_ids:
        and_bits &= pid
        or_bits |= pid
    # A bit is "common" when every piece agrees, i.e. AND bit == OR bit.
    return (~(and_bits ^ or_bits)) & 0xF
