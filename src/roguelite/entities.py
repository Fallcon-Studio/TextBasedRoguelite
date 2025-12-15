"""Core game entities for the text roguelite."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List
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
    statuses: Dict[str, int] = field(default_factory=dict)

    def add_status(self, name: str, duration: int) -> None:
        """Add or refresh a temporary status measured in encounters."""

        current = self.statuses.get(name, 0)
        self.statuses[name] = max(duration, current)

    def has_status(self, name: str) -> bool:
        return self.statuses.get(name, 0) > 0

    def tick_statuses(self) -> List[str]:
        """Reduce duration of active statuses and return any that expired."""

        expired: List[str] = []
        for name in list(self.statuses.keys()):
            self.statuses[name] -= 1
            if self.statuses[name] <= 0:
                expired.append(name)
                del self.statuses[name]
        return expired

    @property
    def status_summary(self) -> str:
        if not self.statuses:
            return "none"
        return ", ".join(f"{key}({turns})" for key, turns in self.statuses.items())

    @property
    def damage_bonus(self) -> int:
        return sum(item.damage_bonus for item in self._equipped_items())

    @property
    def guard_bonus(self) -> int:
        return sum(item.guard_bonus for item in self._equipped_items())

    @property
    def recovery_bonus(self) -> int:
        return sum(item.recovery_bonus for item in self._equipped_items())

    @property
    def guard_value(self) -> int:
        bonus = self.guard_bonus
        if self.has_status("scouted"):
            bonus += 1
        if self.has_status("cursed"):
            bonus -= 1
        return max(0, self.stats.guard + bonus)

    def effective_skill(self) -> int:
        value = self.stats.skill
        if self.has_status("inspired"):
            value += 1
        if self.has_status("cursed"):
            value -= 1
        return max(1, value)

    def effective_awareness(self) -> int:
        value = self.stats.awareness
        if self.has_status("scouted"):
            value += 1
        if self.has_status("inspired"):
            value += 1
        if self.has_status("cursed"):
            value -= 1
        return max(1, value)

    def _equipped_items(self) -> List[Item]:
        equipped: List[Item] = []
        for item in (self.weapon, self.armor, self.trinket):
            if item:
                equipped.append(item)
        return equipped

    def attack(self, target: "Combatant", rng: random.Random) -> str:
        """Performs a basic attack against a target."""
        damage = max(1, (self.effective_skill() + self.damage_bonus) - target.guard_value)
        variance = rng.choice([-1, 0, 0, 1])
        damage = max(1, damage + variance)
        target.stats.health -= damage
        return f"{self.name} strikes {target.name} for {damage} damage."

    def guard(self) -> str:
        """Raises guard to reduce incoming damage for the next turn."""
        self.stats.guard = min(self.stats.guard + 1, 4)
        total_guard = self.guard_value
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
        guard_total = c.guard_value
        summaries.append(
            f"{c.name}: HP {c.stats.health}, ST {c.stats.stamina}, SK {c.stats.skill}, "
            f"AW {c.stats.awareness}, GD {guard_total} | Gear: {gear} | Status: {c.status_summary}"
        )
    return " | ".join(summaries)
