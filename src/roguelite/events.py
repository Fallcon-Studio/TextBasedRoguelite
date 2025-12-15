"""Non-combat encounters and rewards."""

from __future__ import annotations

from typing import Tuple
import random

from .entities import Combatant
from .items import Item, roll_item_drop

EventOutcome = Tuple[str, str, Item | None]


def resolve_event(player: Combatant, danger: int, rng: random.Random) -> EventOutcome:
    """Resolve a non-combat encounter and return narration plus outcome."""
    table = [
        cache_reward,
        scouting_clue,
        ancient_trap,
        meditative_echo,
    ]
    resolver = rng.choice(table)
    return resolver(player, danger, rng)


def cache_reward(player: Combatant, danger: int, rng: random.Random) -> EventOutcome:
    resources = rng.randint(1, 3) + danger
    player.stats.stamina = min(player.stats.stamina + resources, player.stats.awareness + 6)
    player.stats.health = min(player.stats.health + 1, player.stats.awareness + 10)
    item = roll_item_drop(rng, danger)
    narration = (
        "Supply cache: scavenged "
        f"{resources} stamina worth of rations and patched a wound."
    )
    outcome = f"Stamina now {player.stats.stamina}, health {player.stats.health}."
    return narration, outcome, item


def scouting_clue(player: Combatant, danger: int, rng: random.Random) -> EventOutcome:
    bonus_guard = min(2, 1 + danger // 3)
    player.stats.guard = min(player.stats.guard + bonus_guard, 4)
    item = roll_item_drop(rng, max(1, danger - 1)) if rng.random() < 0.4 else None
    narration = "Scouting vantage: you study threats before moving on."
    outcome = f"Guard rises to {player.stats.guard}, improving your next defense."
    return narration, outcome, item


def ancient_trap(player: Combatant, danger: int, rng: random.Random) -> EventOutcome:
    damage = rng.randint(1, 2 + danger)
    player.stats.health -= damage
    consolation_item = roll_item_drop(rng, max(1, danger - 2)) if rng.random() < 0.25 else None
    narration = "Ancient trap: a hidden glyph detonates, searing the area."
    outcome = f"You take {damage} damage (health {player.stats.health})."
    return narration, outcome, consolation_item


def meditative_echo(player: Combatant, danger: int, rng: random.Random) -> EventOutcome:
    skill_gain = 1 if rng.random() < 0.5 else 0
    player.stats.skill += skill_gain
    player.stats.stamina = min(player.stats.stamina + 1, player.stats.awareness + 6)
    item = roll_item_drop(rng, danger + 1) if rng.random() < 0.5 else None
    narration = "Echoing chant: the resonance sharpens your reflexes."
    outcome = f"Skill increases by {skill_gain}, stamina refreshed to {player.stats.stamina}."
    return narration, outcome, item
