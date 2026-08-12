import random

from quarto.game import QuartoGame
from quarto.ai.evaluation import evaluate, extract_features, WEIGHT_SIZE, random_weights
from quarto.ai.search import choose_action
from quarto.ai.players import RandomPlayer, MinimaxPlayer, play_game


def test_extract_features_length_and_empty_board():
    game = QuartoGame()
    feats = extract_features(game.board)
    assert len(feats) == WEIGHT_SIZE
    # empty board: all 10 lines are "0 filled, 4 alive"
    assert feats[0 * 5 + 4] == 10


def test_evaluate_terminal_scores():
    game = QuartoGame()
    weights = [0.0] * WEIGHT_SIZE
    game.winner = 0
    assert evaluate(game, weights, perspective=0) > 0
    assert evaluate(game, weights, perspective=1) < 0

    game2 = QuartoGame()
    game2.is_draw = True
    assert evaluate(game2, weights, perspective=0) == 0.0


def test_choose_action_takes_immediate_win():
    game = QuartoGame()
    # Set up a placement that completes a winning row.
    for piece, cell in [
        (0b0001, (0, 0)),
        (0b0000, (2, 0)),
        (0b0011, (0, 1)),
        (0b0010, (2, 1)),
        (0b1001, (0, 2)),
    ]:
        game.select_piece(piece)
        game.place_piece(*cell)
    # Now it's select phase; hand over the winning piece 0b1011 (tall, shared bit0).
    game.select_piece(0b1011)
    assert game.phase.value == "place"

    weights = random_weights(random.Random(0))
    action = choose_action(game, weights, depth=1)
    assert action == (0, 3)


def test_full_random_vs_random_game_terminates():
    rng = random.Random(42)
    game = play_game(RandomPlayer(rng), RandomPlayer(random.Random(43)), max_plies=100)
    assert game.is_over


def test_minimax_vs_random_plays_full_game():
    weights = random_weights(random.Random(1))
    minimax_player = MinimaxPlayer(weights, depth=1, rng=random.Random(2))
    random_player = RandomPlayer(random.Random(3))
    game = play_game(minimax_player, random_player, max_plies=60)
    assert game.is_over
