"""Feature-based board evaluation, parameterized by a weight vector.

The genetic algorithm evolves this weight vector; the search module uses it
to score non-terminal positions it can't fully resolve by lookahead.

Feature: for every line on the board (10 rows/cols/diagonals, plus the four
2x2 squares if that rule is on) we count how many pieces are placed on it
(`filled`, 0-4) and how many attributes are still shared by all of them
(`alive`, 0-4; 4 means the line is still completely open). We bucket lines
by (filled, alive) and the weight vector holds one coefficient per bucket.
filled == 4 is always terminal (a win or a dead line) so it carries no
useful non-terminal signal and is excluded from the feature vector.
"""

from __future__ import annotations

import random
from typing import List, Sequence

from ..board import Board

MAX_FILLED_FOR_FEATURES = 3  # 0..3 (4 is terminal, handled separately)
MAX_ALIVE = 4  # 0..4

WEIGHT_SIZE = (MAX_FILLED_FOR_FEATURES + 1) * (MAX_ALIVE + 1)  # 4 * 5 = 20

WIN_SCORE = 1_000_000.0


def _bucket_index(filled: int, alive: int) -> int:
    return filled * (MAX_ALIVE + 1) + alive


def extract_features(board: Board) -> List[int]:
    features = [0] * WEIGHT_SIZE
    for line in board.all_lines():
        filled, alive = board.line_status(line)
        if filled > MAX_FILLED_FOR_FEATURES:
            continue  # terminal line, no heuristic signal needed
        features[_bucket_index(filled, alive)] += 1
    return features


def random_weights(rng: random.Random = None) -> List[float]:
    rng = rng or random
    return [rng.uniform(-1.0, 1.0) for _ in range(WEIGHT_SIZE)]


def evaluate(game, weights: Sequence[float], perspective: int) -> float:
    """Score `game` from `perspective` player's point of view.

    Positive = good for `perspective`, negative = good for the opponent.
    """
    if game.winner is not None:
        return WIN_SCORE if game.winner == perspective else -WIN_SCORE
    if game.is_draw:
        return 0.0

    features = extract_features(game.board)
    raw = sum(f * w for f, w in zip(features, weights))
    return raw if game.current_player == perspective else -raw
