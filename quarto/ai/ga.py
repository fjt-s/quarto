"""Genetic algorithm that evolves the weight vector used by evaluation.evaluate.

Each individual is a weight vector (see evaluation.WEIGHT_SIZE). Fitness is
measured by playing games with a depth-limited minimax player driven by that
weight vector: partly round-robin against other individuals in the
population (co-evolution keeps the population honest against itself) and
partly against a random-move baseline (anchors fitness to "does this
actually beat naive play", preventing the population from co-evolving into
a mutually-agreeable-but-weak local optimum).
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from statistics import mean
from typing import Callable, List, Optional, Sequence, Tuple

from .evaluation import WEIGHT_SIZE, random_weights
from .players import MinimaxPlayer, RandomPlayer, play_game

Weights = List[float]


@dataclass
class GAConfig:
    population_size: int = 20
    generations: int = 20
    search_depth: int = 1
    coevolution_rounds: int = 2
    vs_random_games: int = 2
    mutation_rate: float = 0.15
    mutation_sigma: float = 0.3
    elite_count: int = 2
    tournament_size: int = 3
    weight_clamp: float = 5.0
    seed: Optional[int] = None


@dataclass
class GAResult:
    best_weights: Weights
    best_fitness: float
    history: List[dict] = field(default_factory=list)


def _play_and_score(weights_a: Weights, weights_b: Weights, depth: int, rng: random.Random) -> Tuple[float, float]:
    """Play one game; return (score_a, score_b) in {0, 0.5, 1}."""
    game = play_game(
        MinimaxPlayer(weights_a, depth=depth, rng=rng),
        MinimaxPlayer(weights_b, depth=depth, rng=rng),
    )
    if game.winner == 0:
        return 1.0, 0.0
    if game.winner == 1:
        return 0.0, 1.0
    return 0.5, 0.5


def _play_vs_random(weights: Weights, depth: int, rng: random.Random, individual_starts: bool) -> float:
    """Play one game vs a random-move opponent; return the individual's score."""
    if individual_starts:
        game = play_game(MinimaxPlayer(weights, depth=depth, rng=rng), RandomPlayer(rng))
        winning_side = 0
    else:
        game = play_game(RandomPlayer(rng), MinimaxPlayer(weights, depth=depth, rng=rng))
        winning_side = 1
    if game.winner == winning_side:
        return 1.0
    if game.winner is None:
        return 0.5
    return 0.0


def evaluate_population(population: Sequence[Weights], config: GAConfig, rng: random.Random) -> List[float]:
    n = len(population)
    total_score = [0.0] * n
    games_played = [0] * n

    for _ in range(config.coevolution_rounds):
        order = list(range(n))
        rng.shuffle(order)
        for i in range(0, n - 1, 2):
            a, b = order[i], order[i + 1]
            score_a, score_b = _play_and_score(population[a], population[b], config.search_depth, rng)
            total_score[a] += score_a
            total_score[b] += score_b
            games_played[a] += 1
            games_played[b] += 1

    for i in range(n):
        for g in range(config.vs_random_games):
            score = _play_vs_random(population[i], config.search_depth, rng, individual_starts=(g % 2 == 0))
            total_score[i] += score
            games_played[i] += 1

    return [total_score[i] / games_played[i] if games_played[i] else 0.0 for i in range(n)]


def _tournament_select(ranked: Sequence[Tuple[Weights, float]], k: int, rng: random.Random) -> Weights:
    k = min(k, len(ranked))
    contestants = rng.sample(ranked, k)
    return max(contestants, key=lambda pair: pair[1])[0]


def _crossover(parent_a: Weights, parent_b: Weights, rng: random.Random) -> Weights:
    return [rng.choice(pair) for pair in zip(parent_a, parent_b)]


def _mutate(weights: Weights, config: GAConfig, rng: random.Random) -> Weights:
    mutated = list(weights)
    for i in range(len(mutated)):
        if rng.random() < config.mutation_rate:
            mutated[i] += rng.gauss(0, config.mutation_sigma)
            mutated[i] = max(-config.weight_clamp, min(config.weight_clamp, mutated[i]))
    return mutated


def run_ga(config: GAConfig = GAConfig(), on_generation: Optional[Callable[[int, dict], None]] = None) -> GAResult:
    rng = random.Random(config.seed)
    population = [random_weights(rng) for _ in range(config.population_size)]
    history: List[dict] = []
    best_weights, best_fitness = population[0], -1.0

    for generation in range(config.generations):
        fitness = evaluate_population(population, config, rng)
        ranked = sorted(zip(population, fitness), key=lambda pair: pair[1], reverse=True)

        if ranked[0][1] > best_fitness:
            best_weights, best_fitness = ranked[0][0], ranked[0][1]

        stats = {
            "generation": generation,
            "best_fitness": ranked[0][1],
            "mean_fitness": mean(fitness),
        }
        history.append(stats)
        if on_generation:
            on_generation(generation, stats)

        next_population: List[Weights] = [w[:] for w, _ in ranked[: config.elite_count]]
        while len(next_population) < config.population_size:
            parent_a = _tournament_select(ranked, config.tournament_size, rng)
            parent_b = _tournament_select(ranked, config.tournament_size, rng)
            child = _crossover(parent_a, parent_b, rng)
            child = _mutate(child, config, rng)
            next_population.append(child)

        population = next_population

    return GAResult(best_weights=best_weights, best_fitness=best_fitness, history=history)


def save_weights(path: str, weights: Weights) -> None:
    with open(path, "w") as f:
        json.dump({"weights": weights}, f, indent=2)


def load_weights(path: str) -> Weights:
    with open(path) as f:
        data = json.load(f)
    return data["weights"]
