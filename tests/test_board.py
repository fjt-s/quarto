from quarto.board import Board
from quarto.piece import common_mask


def test_common_mask_all_share_height():
    # 0b0000 short-light-square-hollow, 0b0001 tall-light-square-hollow share nothing? actually share color/shape/fill
    a = 0b0000
    b = 0b0001
    mask = common_mask([a, b])
    # they differ only in bit0 (height), so bits 1,2,3 are common -> 0b1110
    assert mask == 0b1110


def test_common_mask_empty_is_full():
    assert common_mask([]) == 0xF


def test_no_winner_on_empty_board():
    board = Board()
    assert board.winning_line() is None


def test_row_win_on_shared_attribute():
    board = Board()
    # all four pieces are "tall" (bit0 = 1): 1, 3, 9, 11
    board.place(0, 0, 0b0001)
    board.place(0, 1, 0b0011)
    board.place(0, 2, 0b1001)
    board.place(0, 3, 0b1011)
    line = board.winning_line()
    assert line is not None
    assert set(line) == {(0, 0), (0, 1), (0, 2), (0, 3)}


def test_full_row_without_shared_attribute_is_not_a_win():
    board = Board()
    # deliberately no shared attribute across all 4
    board.place(0, 0, 0b0000)
    board.place(0, 1, 0b0111)
    board.place(0, 2, 0b1011)
    board.place(0, 3, 0b1101)
    assert board.winning_line() is None


def test_diagonal_win():
    board = Board()
    for i, pid in zip(range(4), [0b0010, 0b0011, 0b0110, 0b1010]):
        board.place(i, i, pid)  # all share color bit (bit1=1)
    line = board.winning_line()
    assert line is not None
    assert set(line) == {(0, 0), (1, 1), (2, 2), (3, 3)}


def test_squares_rule_optional():
    board = Board(squares_rule=True)
    for (r, c), pid in zip([(0, 0), (0, 1), (1, 0), (1, 1)], [0b0100, 0b0101, 0b0110, 0b0111]):
        board.place(r, c, pid)  # all share shape bit (bit2=1)
    assert board.winning_line() is not None

    plain_board = Board(squares_rule=False)
    for (r, c), pid in zip([(0, 0), (0, 1), (1, 0), (1, 1)], [0b0100, 0b0101, 0b0110, 0b0111]):
        plain_board.place(r, c, pid)
    assert plain_board.winning_line() is None


def test_clone_is_independent():
    board = Board()
    board.place(0, 0, 5)
    clone = board.clone()
    clone.place(0, 1, 6)
    assert board.grid[0][1] is None
    assert clone.grid[0][0] == 5
