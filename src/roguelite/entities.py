"""Core game entities for the text roguelite."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import random


@dataclass
class Stats:
    """Represents core stats for any combatant."""

    health: int
    stamina: int
    skill: int
    awareness: int
    guard: int = 0

    def is_alive(self) -> bool:
        return self.health > 0

    def copy(self) -> "Stats":
        return Stats(
            health=self.health,
            stamina=self.stamina,
            skill=self.skill,
            awareness=self.awareness,
            guard=self.guard,
        )


@dataclass
class Combatant:
    """Base combatant with stats and simple combat actions."""

    name: str
    stats: Stats

    def attack(self, target: "Combatant", rng: random.Random) -> str:
        """Performs a basic attack against a target."""
        damage = max(1, self.stats.skill - target.stats.guard)
        variance = rng.choice([-1, 0, 0, 1])
        damage = max(1, damage + variance)
        target.stats.health -= damage
        return f"{self.name} strikes {target.name} for {damage} damage."

    def guard(self) -> str:
        """Raises guard to reduce incoming damage for the next turn."""
        self.stats.guard = min(self.stats.guard + 1, 4)
        return f"{self.name} braces, increasing guard to {self.stats.guard}."

    def recover(self) -> str:
        """Recover stamina and a small amount of health."""
        stamina_gain = 2
        health_gain = 1
        self.stats.stamina = min(self.stats.stamina + stamina_gain, self.stats.awareness + 6)
        self.stats.health = min(self.stats.health + health_gain, self.stats.awareness + 10)
        return (
            f"{self.name} steadies their breathing, recovering {stamina_gain} stamina and "
            f"{health_gain} health."
        )


def describe_combatants(combatants: Iterable[Combatant]) -> str:
    """Returns a summary line describing combatants and their stats."""
    summaries = []
    for c in combatants:
        summaries.append(
            f"{c.name}: HP {c.stats.health}, ST {c.stats.stamina}, SK {c.stats.skill}, AW {c.stats.awareness}, GD {c.stats.guard}"
        )
    return " | ".join(summaries)
