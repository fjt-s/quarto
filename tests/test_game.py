import pytest

from quarto.game import QuartoGame, Phase, IllegalMoveError


def test_initial_state():
    game = QuartoGame()
    assert game.phase == Phase.SELECT
    assert game.current_player == 0
    assert len(game.available_pieces) == 16
    assert not game.is_over


def test_select_then_place_switches_player_and_phase():
    game = QuartoGame()
    game.select_piece(5)
    assert game.phase == Phase.PLACE
    assert game.current_player == 1
    assert game.pending_piece == 5
    assert 5 not in game.available_pieces

    game.place_piece(0, 0)
    assert game.phase == Phase.SELECT
    assert game.current_player == 1  # same player now selects for the opponent
    assert game.board.grid[0][0] == 5


def test_cannot_select_unavailable_piece():
    game = QuartoGame()
    game.select_piece(5)
    game.place_piece(0, 0)
    with pytest.raises(IllegalMoveError):
        game.select_piece(5)


def test_cannot_place_on_occupied_cell():
    game = QuartoGame()
    game.select_piece(0)
    game.place_piece(0, 0)
    game.select_piece(1)
    with pytest.raises(IllegalMoveError):
        game.place_piece(0, 0)


def test_wrong_phase_action_raises():
    game = QuartoGame()
    with pytest.raises(IllegalMoveError):
        game.place_piece(0, 0)


def test_full_game_ends_in_win():
    game = QuartoGame()
    # Build a row win for whoever places the 4th piece of row 0, all "tall".
    moves = [
        (0b0001, (0, 0)),
        (0b0000, (1, 0)),  # filler, not tall, placed elsewhere
        (0b0011, (0, 1)),
        (0b0010, (1, 1)),
        (0b1001, (0, 2)),
        (0b1000, (1, 2)),
        (0b1011, (0, 3)),  # completes the winning row
    ]
    for piece, cell in moves:
        game.select_piece(piece)
        game.place_piece(*cell)
        if game.is_over:
            break

    assert game.is_over
    assert game.winner is not None
    assert game.winning_line is not None
    assert set(game.winning_line) == {(0, 0), (0, 1), (0, 2), (0, 3)}


def test_clone_does_not_affect_original():
    game = QuartoGame()
    game.select_piece(0)
    clone = game.clone()
    clone.place_piece(0, 0)
    assert game.phase == Phase.PLACE
    assert game.board.grid[0][0] is None
    assert clone.board.grid[0][0] == 0
