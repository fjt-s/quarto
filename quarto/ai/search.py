"""Depth-limited minimax (alpha-beta) search driven by the GA-evolved
evaluation function.

Every atomic action (selecting a piece for the opponent, or placing the
pending piece) counts as one ply. `perspective` is fixed to the player who
requested the search; a node is a maximizing node when it's that player's
turn to act, and minimizing otherwise (see evaluation.evaluate).
"""

from __future__ import annotations

import random
from typing import Optional, Sequence, Tuple

from .evaluation import evaluate

INF = float("inf")


def _minimax(game, depth: int, alpha: float, beta: float, perspective: int, weights):
    if game.is_over or depth == 0:
        return evaluate(game, weights, perspective), None

    actions = game.legal_actions()
    maximizing = game.current_player == perspective
    best_value = -INF if maximizing else INF
    best_action = None

    for action in actions:
        child = game.clone()
        child.apply(action)
        value, _ = _minimax(child, depth - 1, alpha, beta, perspective, weights)

        if maximizing:
            if value > best_value:
                best_value, best_action = value, action
            alpha = max(alpha, best_value)
        else:
            if value < best_value:
                best_value, best_action = value, action
            beta = min(beta, best_value)

        if beta <= alpha:
            break

    return best_value, best_action


def choose_action(
    game,
    weights: Sequence[float],
    depth: int = 2,
    rng: Optional[random.Random] = None,
) -> Tuple:
    """Return the best legal action for `game.current_player` given `weights`."""
    actions = game.legal_actions()
    if not actions:
        raise ValueError("no legal actions available")
    if len(actions) == 1:
        return actions[0]

    rng = rng or random
    shuffled = actions[:]
    rng.shuffle(shuffled)  # avoid deterministic bias among equally-good actions

    perspective = game.current_player
    best_value, best_action = -INF, shuffled[0]
    alpha, beta = -INF, INF
    for action in shuffled:
        child = game.clone()
        child.apply(action)
        value, _ = _minimax(child, depth - 1, alpha, beta, perspective, weights)
        if value > best_value:
            best_value, best_action = value, action
        alpha = max(alpha, best_value)

    return best_action
