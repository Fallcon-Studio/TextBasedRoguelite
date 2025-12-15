"""Item and equipment definitions for the roguelite."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence
import random


@dataclass
class Item:
    """Represents an equippable item that modifies combat actions."""

    name: str
    damage_bonus: int = 0
    guard_bonus: int = 0
    recovery_bonus: int = 0
    description: str = ""

    def score(self) -> int:
        """A heuristic score used to select the best item to auto-equip."""
        return (self.damage_bonus * 3) + (self.guard_bonus * 2) + self.recovery_bonus

    def summary(self) -> str:
        parts: List[str] = []
        if self.damage_bonus:
            parts.append(f"+{self.damage_bonus} dmg")
        if self.guard_bonus:
            parts.append(f"+{self.guard_bonus} guard")
        if self.recovery_bonus:
            parts.append(f"+{self.recovery_bonus} recovery")
        bonuses = ", ".join(parts) or "no bonus"
        return f"{self.name} ({bonuses})"


def roll_item_drop(rng: random.Random, danger: int) -> Item | None:
    """Roll for an item drop based on danger level."""

    drop_chance = min(0.2 + (danger * 0.1), 0.75)
    if rng.random() > drop_chance:
        return None

    table: Sequence[Item]
    if danger >= 5:
        table = HIGH_TIER_ITEMS
    elif danger >= 3:
        table = MID_TIER_ITEMS
    else:
        table = LOW_TIER_ITEMS

    template = rng.choice(table)
    return Item(
        name=template.name,
        damage_bonus=template.damage_bonus,
        guard_bonus=template.guard_bonus,
        recovery_bonus=template.recovery_bonus,
        description=template.description,
    )


LOW_TIER_ITEMS: Sequence[Item] = (
    Item("Rusted Shiv", damage_bonus=1, description="A chipped blade that cuts deeper than it looks."),
    Item("Tattered Cloak", guard_bonus=1, description="Layers of fabric that blunt stray blows."),
    Item("Field Rations", recovery_bonus=1, description="Boosts stamina and focus after exertion."),
)

MID_TIER_ITEMS: Sequence[Item] = (
    Item("Balanced Spear", damage_bonus=2, description="Well-weighted, perfect for precise strikes."),
    Item("Iron Buckler", guard_bonus=2, description="Reliable cover that catches incoming hits."),
    Item(
        "Reinforced Harness",
        damage_bonus=1,
        guard_bonus=1,
        description="Keeps movement sharp while protecting vital spots.",
    ),
    Item(
        "Medicinal Kit",
        recovery_bonus=2,
        description="Herbs and bandages accelerate recovery between blows.",
    ),
)

HIGH_TIER_ITEMS: Sequence[Item] = (
    Item(
        "Edge of Echoes",
        damage_bonus=3,
        description="Resonating blade that finds openings effortlessly.",
    ),
    Item(
        "Guardian's Bulwark",
        guard_bonus=3,
        description="Heavy plating that turns aside ferocious strikes.",
    ),
    Item(
        "Battle Hymn Charm",
        damage_bonus=1,
        guard_bonus=1,
        recovery_bonus=1,
        description="A talisman that steadies breath and timing alike.",
    ),
)


def best_item(items: Iterable[Item]) -> Item | None:
    """Return the highest scoring item from a collection."""

    best: Item | None = None
    for item in items:
        if best is None or item.score() > best.score():
            best = item
    return best
