"""Core game entities for the text roguelite."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List
import random

from .items import Consumable, Item


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
    inventory: List[Item] = field(default_factory=list)
    consumables: List[Consumable] = field(default_factory=list)
    weapon: Item | None = None
    armor: Item | None = None
    trinket: Item | None = None

    @property
    def damage_bonus(self) -> int:
        return sum(item.damage_bonus for item in self._equipped_items())

    @property
    def guard_bonus(self) -> int:
        return sum(item.guard_bonus for item in self._equipped_items())

    @property
    def recovery_bonus(self) -> int:
        return sum(item.recovery_bonus for item in self._equipped_items())

    def _equipped_items(self) -> List[Item]:
        equipped: List[Item] = []
        for item in (self.weapon, self.armor, self.trinket):
            if item:
                equipped.append(item)
        return equipped

    def attack(self, target: "Combatant", rng: random.Random) -> str:
        """Performs a basic attack against a target."""
        damage = max(1, (self.stats.skill + self.damage_bonus) - (target.stats.guard + target.guard_bonus))
        variance = rng.choice([-1, 0, 0, 1])
        damage = max(1, damage + variance)
        target.stats.health -= damage
        return f"{self.name} strikes {target.name} for {damage} damage."

    def guard(self) -> str:
        """Raises guard to reduce incoming damage for the next turn."""
        self.stats.guard = min(self.stats.guard + 1, 4)
        total_guard = self.stats.guard + self.guard_bonus
        return f"{self.name} braces, increasing guard to {total_guard}."

    def recover(self) -> str:
        """Recover stamina and a small amount of health."""
        stamina_gain = 2 + self.recovery_bonus
        health_gain = 1 + max(0, self.recovery_bonus - 1)
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
        gear_pieces = [
            c.weapon.summary() if c.weapon else "bare hands",
            c.armor.summary() if c.armor else "no armor",
            c.trinket.summary() if c.trinket else "no trinket",
        ]
        gear = "/".join(gear_pieces)
        guard_total = c.stats.guard + c.guard_bonus
        summaries.append(
            f"{c.name}: HP {c.stats.health}, ST {c.stats.stamina}, SK {c.stats.skill}, "
            f"AW {c.stats.awareness}, GD {guard_total} | Gear: {gear}"
        )
    return " | ".join(summaries)
