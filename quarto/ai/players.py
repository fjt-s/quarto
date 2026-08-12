"""Player interfaces used by both the GA training loop and the web app."""

from __future__ import annotations

import random
from typing import Optional, Sequence

from .search import choose_action


class Player:
    """Base interface: given a game state, return a legal action."""

    def act(self, game):
        raise NotImplementedError


class RandomPlayer(Player):
    """Picks uniformly among legal actions. Useful as a GA baseline opponent."""

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()

    def act(self, game):
        return self.rng.choice(game.legal_actions())


class MinimaxPlayer(Player):
    """Depth-limited minimax using a (typically GA-evolved) weight vector."""

    def __init__(self, weights: Sequence[float], depth: int = 2, rng: Optional[random.Random] = None):
        self.weights = list(weights)
        self.depth = depth
        self.rng = rng or random.Random()

    def act(self, game):
        return choose_action(game, self.weights, depth=self.depth, rng=self.rng)


def play_game(player0: Player, player1: Player, squares_rule: bool = False, max_plies: int = 200):
    """Run a full game between two Player objects. Returns the finished game."""
    from ..game import QuartoGame

    game = QuartoGame(squares_rule=squares_rule)
    players = (player0, player1)
    plies = 0
    while not game.is_over and plies < max_plies:
        action = players[game.current_player].act(game)
        game.apply(action)
        plies += 1
    return game
