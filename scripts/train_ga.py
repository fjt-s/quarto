#!/usr/bin/env python3
"""Train the Quarto bot's evaluation weights with a genetic algorithm.

Example:
    python scripts/train_ga.py --generations 40 --population 30 --depth 2 \
        --out weights/best.json
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quarto.ai.ga import GAConfig, run_ga, save_weights


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--population", type=int, default=24, help="population size")
    parser.add_argument("--generations", type=int, default=30, help="number of generations")
    parser.add_argument("--depth", type=int, default=1, help="minimax search depth used during fitness games")
    parser.add_argument("--coevolution-rounds", type=int, default=2, help="round-robin rounds per generation")
    parser.add_argument("--vs-random-games", type=int, default=2, help="games vs random baseline per individual")
    parser.add_argument("--mutation-rate", type=float, default=0.15)
    parser.add_argument("--mutation-sigma", type=float, default=0.3)
    parser.add_argument("--elite-count", type=int, default=2)
    parser.add_argument("--tournament-size", type=int, default=3)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--out", type=str, default="weights/best.json", help="output path for the best weights")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = GAConfig(
        population_size=args.population,
        generations=args.generations,
        search_depth=args.depth,
        coevolution_rounds=args.coevolution_rounds,
        vs_random_games=args.vs_random_games,
        mutation_rate=args.mutation_rate,
        mutation_sigma=args.mutation_sigma,
        elite_count=args.elite_count,
        tournament_size=args.tournament_size,
        seed=args.seed,
    )

    def on_generation(generation: int, stats: dict) -> None:
        print(
            f"gen {generation + 1:3d}/{config.generations}  "
            f"best={stats['best_fitness']:.3f}  mean={stats['mean_fitness']:.3f}"
        )

    result = run_ga(config, on_generation=on_generation)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    save_weights(args.out, result.best_weights)
    print(f"\nBest fitness: {result.best_fitness:.3f}")
    print(f"Saved weights to {args.out}")


if __name__ == "__main__":
    main()
