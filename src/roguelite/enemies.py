"""Enemy archetype definitions and behaviors."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Iterable, Tuple

from .entities import Combatant, Stats


Intent = Tuple[str, str]
OnHitEffect = Callable[[Combatant, Combatant, random.Random], str | None]


@dataclass
class EnemyTemplate:
    """Configures stats, behavior, and rewards for an enemy archetype."""

    key: str
    title: str
    description: str
    base_stats: Stats
    scaling: Stats
    preferred_biomes: Iterable[str]
    loot_multiplier: float
    xp_value: float
    behavior: "BehaviorRoutine"
    on_hit_effect: OnHitEffect

    def spawn(self, danger: int, rng: random.Random) -> Combatant:
        """Instantiate a combatant scaled by location danger."""

        stats = Stats(
            health=self.base_stats.health + self.scaling.health * max(0, danger - 1),
            stamina=self.base_stats.stamina + self.scaling.stamina * max(0, danger - 1),
            skill=self.base_stats.skill + self.scaling.skill * max(0, danger - 1),
            awareness=self.base_stats.awareness + self.scaling.awareness * max(0, danger - 1),
        )
        name_suffix = rng.choice(["strider", "prowler", "fiend", "raider", "stalker"])
        return Combatant(name=f"{self.title} {name_suffix}", stats=stats)


class BehaviorRoutine:
    """Determines an enemy action and the intent telegraphed to the player."""

    def decide(self, enemy: Combatant, player: Combatant, rng: random.Random) -> Intent:
        raise NotImplementedError


class SkirmisherRoutine(BehaviorRoutine):
    def decide(self, enemy: Combatant, player: Combatant, rng: random.Random) -> Intent:
        if enemy.stats.stamina <= 1:
            return "recover", "backpedals to regain footing"
        if player.stats.guard <= 1 or enemy.stats.stamina >= 3:
            return "attack", "darts in for a decisive strike"
        if rng.random() < 0.4:
            return "attack", "lashes out before you can reset"
        return "guard", "circles warily, blades ready to counter"


class BruteRoutine(BehaviorRoutine):
    def decide(self, enemy: Combatant, player: Combatant, rng: random.Random) -> Intent:
        if enemy.stats.stamina <= 0:
            return "recover", "huffs to catch a breath"
        if enemy.stats.health > enemy.stats.awareness and enemy.stats.stamina >= 2:
            return "attack", "winds up for a crushing blow"
        if player.stats.guard >= 2 and rng.random() < 0.5:
            return "guard", "raises defenses, daring you to approach"
        if enemy.stats.health < max(4, enemy.stats.awareness // 2) and rng.random() < 0.4:
            return "recover", "tries to shrug off pain"
        return "attack", "barrels forward without hesitation"


class CasterRoutine(BehaviorRoutine):
    def decide(self, enemy: Combatant, player: Combatant, rng: random.Random) -> Intent:
        if enemy.stats.stamina <= 1:
            return "recover", "chants to draw in energy"
        if player.stats.guard >= 3:
            return "guard", "raises a shimmering ward"
        if player.stats.health <= 4 and rng.random() < 0.6:
            return "attack", "lets loose a focused hex"
        if rng.random() < 0.3:
            return "guard", "anchors themselves with a rune"
        return "attack", "gathers volatile power to fling your way"


def _skirmisher_on_hit(enemy: Combatant, player: Combatant, rng: random.Random) -> str | None:
    if player.stats.guard <= 0:
        return None
    player.stats.guard = max(0, player.stats.guard - 1)
    return f"{enemy.name}'s feint strips away your guard!"


def _brute_on_hit(enemy: Combatant, player: Combatant, rng: random.Random) -> str | None:
    if player.stats.stamina <= 0:
        return None
    drain = 1 if player.stats.stamina <= 2 else 2 if rng.random() < 0.35 else 1
    player.stats.stamina = max(0, player.stats.stamina - drain)
    return f"The impact staggers you, draining {drain} stamina!"


def _caster_on_hit(enemy: Combatant, player: Combatant, rng: random.Random) -> str | None:
    burn = 1 if rng.random() < 0.5 else 2
    player.stats.health -= burn
    return f"Hexfire lingers, burning you for {burn} extra damage!"


ENEMY_TEMPLATES: tuple[EnemyTemplate, ...] = (
    EnemyTemplate(
        key="skirmisher",
        title="Skirmisher",
        description="quick strikers that punish overextending foes",
        base_stats=Stats(health=7, stamina=8, skill=4, awareness=4),
        scaling=Stats(health=1, stamina=1, skill=1, awareness=1),
        preferred_biomes=("ruins", "wetlands"),
        loot_multiplier=1.0,
        xp_value=1.0,
        behavior=SkirmisherRoutine(),
        on_hit_effect=_skirmisher_on_hit,
    ),
    EnemyTemplate(
        key="brute",
        title="Brute",
        description="relentless maulers that trade blows for exhaustion",
        base_stats=Stats(health=9, stamina=7, skill=3, awareness=3),
        scaling=Stats(health=2, stamina=1, skill=1, awareness=1),
        preferred_biomes=("ruins", "caverns"),
        loot_multiplier=1.3,
        xp_value=1.2,
        behavior=BruteRoutine(),
        on_hit_effect=_brute_on_hit,
    ),
    EnemyTemplate(
        key="caster",
        title="Hexcaster",
        description="mystics whose spells punish the unwary",
        base_stats=Stats(health=6, stamina=7, skill=4, awareness=5),
        scaling=Stats(health=1, stamina=1, skill=1, awareness=2),
        preferred_biomes=("wetlands", "caverns"),
        loot_multiplier=1.15,
        xp_value=1.4,
        behavior=CasterRoutine(),
        on_hit_effect=_caster_on_hit,
    ),
)


def pick_enemy_template(biome_key: str, danger: int, rng: random.Random) -> EnemyTemplate:
    """Select an archetype based on biome, danger, and randomness."""

    weights = []
    for template in ENEMY_TEMPLATES:
        weight = 1.0
        if biome_key in template.preferred_biomes:
            weight += 0.65
        if template.key == "brute" and danger >= 4:
            weight += 0.5
        if template.key == "caster" and danger >= 3:
            weight += 0.35
        if template.key == "skirmisher" and danger <= 2:
            weight += 0.35
        weights.append(weight)
    return rng.choices(list(ENEMY_TEMPLATES), weights=weights, k=1)[0]
