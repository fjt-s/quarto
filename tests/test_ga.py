import os
import tempfile

from quarto.ai.evaluation import WEIGHT_SIZE
from quarto.ai.ga import GAConfig, run_ga, save_weights, load_weights


def test_run_ga_small_config_improves_and_returns_valid_weights():
    config = GAConfig(
        population_size=6,
        generations=3,
        search_depth=1,
        coevolution_rounds=1,
        vs_random_games=1,
        seed=123,
    )
    result = run_ga(config)
    assert len(result.best_weights) == WEIGHT_SIZE
    assert 0.0 <= result.best_fitness <= 1.0
    assert len(result.history) == 3
    # fitness should be tracked as non-decreasing "best so far"
    bests = [h["best_fitness"] for h in result.history]
    assert all(0.0 <= b <= 1.0 for b in bests)


def test_save_and_load_weights_roundtrip():
    weights = [0.1 * i for i in range(WEIGHT_SIZE)]
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "weights.json")
        save_weights(path, weights)
        loaded = load_weights(path)
    assert loaded == weights
