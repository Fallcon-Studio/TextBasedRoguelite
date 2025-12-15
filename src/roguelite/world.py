"""Procedural world generation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List
import random


@dataclass
class Location:
    """A logical location in the world."""

    name: str
    danger: int
    encounter: str  # enemy, rest, event
    description: str


FLAVORS = [
    "shattered towers and drifting ash",
    "silent wetlands wrapped in mist",
    "fractured caverns buzzing with faint echoes",
    "glimmering basalt plains warmed by hidden vents",
    "ivy-choked ruins turned into a den of beasts",
]


ENCOUNTERS = ["enemy", "rest", "event"]


def generate_world(seed: int | None, steps: int) -> List[Location]:
    """Generate a list of locations for the run."""
    rng = random.Random(seed)
    locations: List[Location] = []
    for idx in range(steps):
        encounter = rng.choices(ENCOUNTERS, weights=[0.5, 0.2, 0.3], k=1)[0]
        danger = rng.randint(1, 4) + idx // 3
        flavor = rng.choice(FLAVORS)
        name = f"Node {idx + 1}"
        locations.append(
            Location(
                name=name,
                danger=danger,
                encounter=encounter,
                description=f"You reach {flavor}. Threat level {danger}.",
            )
        )
    return locations
