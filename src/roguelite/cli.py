"""Command-line entry point for the text-based roguelite."""

from __future__ import annotations

import argparse
from typing import Optional

from .game import Game, GameSettings
from .gui import launch_gui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Procedural text roguelite")
    parser.add_argument("--seed", type=int, default=None, help="Seed for deterministic runs")
    parser.add_argument("--steps", type=int, default=6, help="Number of locations to traverse")
    parser.add_argument("--auto", action="store_true", help="Use recommended automatic actions")
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = GameSettings(seed=args.seed, steps=args.steps, auto=args.auto)
    if settings.auto:
        game = Game(settings)
        game.play()
        return

    launch_gui(settings)


if __name__ == "__main__":
    main()
