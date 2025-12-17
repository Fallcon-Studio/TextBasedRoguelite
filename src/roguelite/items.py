"""Item, equipment, and consumable definitions for the roguelite."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Sequence, TYPE_CHECKING
import random

if TYPE_CHECKING:  # pragma: no cover - for type checking without circular import
    from .entities import Combatant
else:  # pragma: no cover - runtime fallback to satisfy type aliases
    Combatant = Any


ConsumableEffect = Callable[[Combatant, Combatant | None, random.Random], str]


@dataclass
class Item:
    """Represents an equippable item that modifies combat actions."""

    name: str
    slot: str
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
        return f"{self.name} [{self.slot}] ({bonuses})"


@dataclass
class Consumable:
    """Represents a limited-use item with an immediate effect."""

    name: str
    description: str
    charges: int
    requires_target: bool
    on_use: ConsumableEffect

    def summary(self) -> str:
        return f"{self.name} (x{self.charges})"

    def use(self, user: "Combatant", target: "Combatant" | None, rng: random.Random) -> str:
        if self.charges <= 0:
            return f"{self.name} has no charges left."
        self.charges -= 1
        effect_text = self.on_use(user, target, rng)
        return f"{self.name}: {effect_text} (remaining {self.charges})"


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
        slot=template.slot,
        damage_bonus=template.damage_bonus,
        guard_bonus=template.guard_bonus,
        recovery_bonus=template.recovery_bonus,
        description=template.description,
    )


LOW_TIER_ITEMS: Sequence[Item] = (
    Item(
        "Rusted Shiv",
        slot="weapon",
        damage_bonus=1,
        description="A chipped blade that cuts deeper than it looks.",
    ),
    Item(
        "Tattered Cloak",
        slot="armor",
        guard_bonus=1,
        description="Layers of fabric that blunt stray blows.",
    ),
    Item(
        "Field Rations",
        slot="trinket",
        recovery_bonus=1,
        description="Boosts stamina and focus after exertion.",
    ),
)

MID_TIER_ITEMS: Sequence[Item] = (
    Item(
        "Balanced Spear",
        slot="weapon",
        damage_bonus=2,
        description="Well-weighted, perfect for precise strikes.",
    ),
    Item(
        "Iron Buckler",
        slot="armor",
        guard_bonus=2,
        description="Reliable cover that catches incoming hits.",
    ),
    Item(
        "Reinforced Harness",
        slot="armor",
        damage_bonus=1,
        guard_bonus=1,
        description="Keeps movement sharp while protecting vital spots.",
    ),
    Item(
        "Medicinal Kit",
        slot="trinket",
        recovery_bonus=2,
        description="Herbs and bandages accelerate recovery between blows.",
    ),
)

HIGH_TIER_ITEMS: Sequence[Item] = (
    Item(
        "Edge of Echoes",
        slot="weapon",
        damage_bonus=3,
        description="Resonating blade that finds openings effortlessly.",
    ),
    Item(
        "Guardian's Bulwark",
        slot="armor",
        guard_bonus=3,
        description="Heavy plating that turns aside ferocious strikes.",
    ),
    Item(
        "Battle Hymn Charm",
        slot="trinket",
        damage_bonus=1,
        guard_bonus=1,
        recovery_bonus=1,
        description="A talisman that steadies breath and timing alike.",
    ),
)


def best_item(items: Iterable[Item], slot: str | None = None) -> Item | None:
    """Return the highest scoring item from a collection, optionally filtered by slot."""

    best: Item | None = None
    for item in items:
        if slot and item.slot != slot:
            continue
        if best is None or item.score() > best.score():
            best = item
    return best


def _healing_draught(user: "Combatant", _: "Combatant" | None, rng: random.Random) -> str:
    heal = 4 + rng.randint(0, 2)
    user.stats.health = min(user.stats.health + heal, user.stats.awareness + 10)
    return f"restores {heal} health"


def _stamina_tonic(user: "Combatant", _: "Combatant" | None, rng: random.Random) -> str:
    stamina = 3 + rng.randint(0, 1)
    user.stats.stamina = min(user.stats.stamina + stamina, user.stats.awareness + 6)
    return f"recovers {stamina} stamina"


def _shock_grenade(_: "Combatant", target: "Combatant" | None, rng: random.Random) -> str:
    if target is None:
        return "fizzles with no target"
    damage = 3 + rng.randint(0, 2)
    target.stats.health -= damage
    target.stats.guard = max(0, target.stats.guard - 1)
    return f"detonates for {damage} damage and rattles their guard"


def _focus_charm(user: "Combatant", _: "Combatant" | None, rng: random.Random) -> str:
    skill_gain = 1 if rng.random() < 0.75 else 2
    user.stats.skill += skill_gain
    user.stats.awareness += 1
    return f"sharpens focus (+{skill_gain} skill, +1 awareness)"


CONSUMABLES: Sequence[Consumable] = (
    Consumable(
        name="Healing Draught",
        description="A restorative potion brewed from moss and moonlight.",
        charges=2,
        requires_target=False,
        on_use=_healing_draught,
    ),
    Consumable(
        name="Stamina Tonic",
        description="Invigorating herbs that push exhaustion away.",
        charges=2,
        requires_target=False,
        on_use=_stamina_tonic,
    ),
    Consumable(
        name="Shock Grenade",
        description="Crackling sphere that stuns anything it hits.",
        charges=1,
        requires_target=True,
        on_use=_shock_grenade,
    ),
    Consumable(
        name="Focus Charm",
        description="A quick ritual that steadies the mind.",
        charges=1,
        requires_target=False,
        on_use=_focus_charm,
    ),
)


def roll_consumable_drop(rng: random.Random, danger: int) -> Consumable | None:
    """Roll for a consumable drop; rarer than equipment but highly impactful."""

    drop_chance = min(0.15 + (danger * 0.05), 0.5)
    if rng.random() > drop_chance:
        return None

    template = rng.choice(CONSUMABLES)
    return Consumable(
        name=template.name,
        description=template.description,
        charges=template.charges,
        requires_target=template.requires_target,
        on_use=template.on_use,
    )
