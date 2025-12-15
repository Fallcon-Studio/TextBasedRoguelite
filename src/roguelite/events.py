"""Non-combat encounters and branching event resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Sequence, Tuple, TYPE_CHECKING
import random

from .entities import Combatant
from .items import Consumable, Item, roll_consumable_drop, roll_item_drop

if TYPE_CHECKING:  # pragma: no cover - for import clarity only
    from .game import Game
    from .world import Location


@dataclass
class EventOutcome:
    """Narrative and mechanical result of choosing an event option."""

    narration: str
    outcome: str
    item: Item | None = None
    consumable: Consumable | None = None
    status_effects: List[Tuple[str, int, str]] = field(default_factory=list)


@dataclass
class EventOption:
    """A selectable branch within an event scenario."""

    title: str
    detail: str
    risk: str  # descriptive tag: safe, risky, trade
    resolver: Callable[[Combatant, "Game", "Location", random.Random], EventOutcome]


@dataclass
class EventScenario:
    """A themed event with options and biome targeting."""

    title: str
    intro: str
    options: List[EventOption]
    biome_keys: Sequence[str] | None = None


# === Event option helpers ===

def _apply_skill_check(
    player: Combatant,
    threshold: int,
    rng: random.Random,
    bonus: int = 0,
) -> bool:
    roll = rng.randint(2, 6) + player.effective_skill() + player.effective_awareness() + bonus
    return roll >= threshold


def _status_effect(name: str, duration: int, source: str) -> Tuple[str, int, str]:
    return (name, duration, source)


# === Scenario builders ===

def ruins_archive() -> EventScenario:
    def study_inscriptions(player: Combatant, game: "Game", location: "Location", rng: random.Random) -> EventOutcome:
        difficulty = 11 + location.danger
        success = _apply_skill_check(player, difficulty, rng, bonus=1 if player.trinket else 0)
        if success:
            item = roll_item_drop(rng, location.danger + 1)
            return EventOutcome(
                narration="You read the fractured murals, piecing together forgotten tactics.",
                outcome="Insight flows through you; the scripture inspires your stance.",
                item=item,
                status_effects=[_status_effect("inspired", 2, "studying war-songs")],
            )
        player.stats.health -= max(1, location.danger - 1)
        return EventOutcome(
            narration="The glyphs flare angrily and backlash against your mind.",
            outcome=f"You reel, suffering a curse (health {player.stats.health}).",
            status_effects=[_status_effect("cursed", 2, "hexed murals")],
        )

    def pry_open_cache(player: Combatant, game: "Game", location: "Location", rng: random.Random) -> EventOutcome:
        stamina_cost = max(1, location.danger // 2)
        player.stats.stamina = max(0, player.stats.stamina - stamina_cost)
        variance = rng.randint(-1, 2)
        power_score = player.effective_skill() + player.damage_bonus + variance
        if power_score >= location.danger + 2:
            item = roll_item_drop(rng, location.danger + 1)
            consumable = roll_consumable_drop(rng, location.danger)
            return EventOutcome(
                narration="The stone lid groans aside, revealing preserved tools.",
                outcome=f"Your exertion pays off. You spend {stamina_cost} stamina to seize the cache.",
                item=item,
                consumable=consumable,
                status_effects=[_status_effect("scouted", 2, "surveyed treasure room")],
            )
        damage = max(1, location.danger - variance)
        player.stats.health -= damage
        return EventOutcome(
            narration="A load-bearing pillar snaps. Dust and debris crash onto you.",
            outcome=f"The attempt backfires for {damage} damage (health {player.stats.health}).",
            status_effects=[_status_effect("cursed", 1, "falling masonry")],
        )

    def chart_rubble(player: Combatant, game: "Game", location: "Location", rng: random.Random) -> EventOutcome:
        stamina_spent = 1
        player.stats.stamina = max(0, player.stats.stamina - stamina_spent)
        guard_boost = min(2, 1 + (1 if player.has_status("scouted") else 0))
        player.stats.guard = min(player.stats.guard + guard_boost, 4)
        return EventOutcome(
            narration="You mark safe walkways and loose stones for the path ahead.",
            outcome=(
                f"You trade {stamina_spent} stamina for awareness of ambush angles "
                f"(guard +{guard_boost})."
            ),
            status_effects=[_status_effect("scouted", 3, "mapped hallways")],
        )

    return EventScenario(
        title="Shattered Archive",
        intro="Ruined vaults loom with cracked murals and hidden recesses.",
        biome_keys=["ruins"],
        options=[
            EventOption("Study inscriptions", "Risk a mental duel with the old wards.", "risky", study_inscriptions),
            EventOption("Pry open cache", "Force a sealed alcove, spending stamina for loot.", "balanced", pry_open_cache),
            EventOption("Chart the rubble", "Scout safe lines of travel, trading effort for safety.", "safe", chart_rubble),
        ],
    )


def wetlands_shrine() -> EventScenario:
    def harvest_lotus(player: Combatant, game: "Game", location: "Location", rng: random.Random) -> EventOutcome:
        difficulty = 10 + location.danger
        armor_help = 1 if player.armor else 0
        success = _apply_skill_check(player, difficulty - armor_help, rng)
        if success:
            consumable = roll_consumable_drop(rng, location.danger + 1)
            return EventOutcome(
                narration="You balance along the stones, clipping glowing lotus buds.",
                outcome="The harvested herbs bolster your kit and steady your mind.",
                consumable=consumable,
                status_effects=[_status_effect("inspired", 1, "botanical insight")],
            )
        damage = max(1, location.danger - armor_help)
        player.stats.health -= damage
        return EventOutcome(
            narration="The bog water surges. A leeching current drags you under.",
            outcome=f"You escape but feel cursed and lose {damage} health (health {player.stats.health}).",
            status_effects=[_status_effect("cursed", 2, "swamp curse")],
        )

    def leave_offering(player: Combatant, game: "Game", location: "Location", rng: random.Random) -> EventOutcome:
        if player.consumables:
            player.consumables.pop(0)
            blessing = roll_item_drop(rng, max(1, location.danger - 1))
            return EventOutcome(
                narration="You leave supplies at a mossy idol; the waters still in approval.",
                outcome="The shrine returns the favor with a guiding current.",
                item=blessing,
                status_effects=[_status_effect("scouted", 2, "guided by currents")],
            )
        return EventOutcome(
            narration="Empty-handed, you whisper a promise you cannot keep.",
            outcome="The bog is unimpressed. Nothing changes, but you move on warily.",
            status_effects=[_status_effect("scouted", 1, "cautious pacing")],
        )

    def chase_wisps(player: Combatant, game: "Game", location: "Location", rng: random.Random) -> EventOutcome:
        wisp_test = rng.randint(1, 4) + player.effective_awareness()
        if wisp_test >= location.danger + 3:
            item = roll_item_drop(rng, location.danger + 2)
            return EventOutcome(
                narration="You follow flickering lights to a cache tangled in reeds.",
                outcome="A risky pursuit pays off; you feel invigorated by the hunt.",
                item=item,
                status_effects=[_status_effect("inspired", 2, "trickster pursuit")],
            )
        player.stats.stamina = max(0, player.stats.stamina - 2)
        return EventOutcome(
            narration="The lights vanish. You slog in circles through sucking mud.",
            outcome="Exhaustion sets in (lose 2 stamina) and the chill leaves you cursed.",
            status_effects=[_status_effect("cursed", 1, "bog misdirection")],
        )

    return EventScenario(
        title="Bog Shrine",
        intro="An altar sits above a flooded causeway, wisps dancing between reeds.",
        biome_keys=["wetlands"],
        options=[
            EventOption("Harvest lotus", "Collect luminous herbs for later use.", "balanced", harvest_lotus),
            EventOption("Leave an offering", "Trade a consumable for the shrine's favor.", "trade", leave_offering),
            EventOption("Chase will-o'-wisps", "Pursue mysterious lights for a hidden reward.", "risky", chase_wisps),
        ],
    )


def cavern_echoes() -> EventScenario:
    def ride_thermal(player: Combatant, game: "Game", location: "Location", rng: random.Random) -> EventOutcome:
        stamina_gain = 1 + rng.randint(0, 1)
        player.stats.stamina = min(player.stats.stamina + stamina_gain, player.stats.awareness + 6)
        return EventOutcome(
            narration="You let an updraft carry your glider-cloth through a narrow shaft.",
            outcome=f"The lift restores {stamina_gain} stamina and scouts exits.",
            status_effects=[_status_effect("scouted", 2, "mapped vents")],
        )

    def mine_crystals(player: Combatant, game: "Game", location: "Location", rng: random.Random) -> EventOutcome:
        pick_bonus = 1 if player.weapon else 0
        success = _apply_skill_check(player, 10 + location.danger, rng, bonus=pick_bonus)
        if success:
            item = roll_item_drop(rng, location.danger + 2)
            return EventOutcome(
                narration="Your strikes split a resonant crystal vein.",
                outcome="The shards sing to your nerves, sharpening your focus.",
                item=item,
                status_effects=[_status_effect("inspired", 2, "harmonic resonance")],
            )
        backlash = max(1, location.danger - pick_bonus)
        player.stats.health -= backlash
        return EventOutcome(
            narration="A crystal explodes, rattling your bones with discordant sound.",
            outcome=f"You are rattled and cursed, losing {backlash} health (health {player.stats.health}).",
            status_effects=[_status_effect("cursed", 2, "resonant backlash")],
        )

    def listen_for_paths(player: Combatant, game: "Game", location: "Location", rng: random.Random) -> EventOutcome:
        awareness_test = player.effective_awareness() + rng.randint(1, 4)
        if awareness_test >= location.danger + 2:
            return EventOutcome(
                narration="You attune to the echoes, charting enemy movements ahead.",
                outcome="The sound-map inspires you to exploit openings first.",
                status_effects=[_status_effect("scouted", 2, "echo mapping"), _status_effect("inspired", 1, "rhythmic focus")],
            )
        return EventOutcome(
            narration="The echoes overlap confusingly; you strain to parse them.",
            outcome="No clear path emerges, but the practice steels your guard.",
            status_effects=[_status_effect("scouted", 1, "nervous pacing")],
        )

    return EventScenario(
        title="Echoing Hollows",
        intro="Vent chimneys roar and crystal lattices glitter with dull resonance.",
        biome_keys=["caverns"],
        options=[
            EventOption("Ride a thermal", "Glide on rising heat to glimpse nearby tunnels.", "safe", ride_thermal),
            EventOption("Mine crystals", "Strike a crystal vein for rare shards.", "risky", mine_crystals),
            EventOption("Listen for paths", "Use sound to trace threats and openings.", "balanced", listen_for_paths),
        ],
    )


def wandering_cartographer() -> EventScenario:
    def trade_routes(player: Combatant, game: "Game", location: "Location", rng: random.Random) -> EventOutcome:
        if player.inventory:
            player.inventory.pop()
            reward = roll_item_drop(rng, max(1, location.danger - 1))
            return EventOutcome(
                narration="The cartographer barters maps for one of your spare tools.",
                outcome="You exchange gear for a detailed chart of the region.",
                item=reward,
                status_effects=[_status_effect("scouted", 2, "borrowed map")],
            )
        return EventOutcome(
            narration="With little to trade, you rely on shared stories instead.",
            outcome="The cartographer still marks a shortcut out of kindness.",
            status_effects=[_status_effect("scouted", 1, "charity shortcut")],
        )

    def spar_for_tips(player: Combatant, game: "Game", location: "Location", rng: random.Random) -> EventOutcome:
        stamina_cost = 1
        player.stats.stamina = max(0, player.stats.stamina - stamina_cost)
        duel_score = player.effective_skill() + rng.randint(1, 4)
        if duel_score >= location.danger + 2:
            player.stats.skill += 1
            return EventOutcome(
                narration="A quick spar sharpens your blade-work under watchful eyes.",
                outcome="You impress the cartographer, gaining a tip and a skill boost (+1 skill).",
                status_effects=[_status_effect("inspired", 2, "friendly duel")],
            )
        player.stats.health -= 1
        return EventOutcome(
            narration="Your footing slips in the bout.",
            outcome="Bruised but wiser (lose 1 health) and cursed by doubt.",
            status_effects=[_status_effect("cursed", 1, "rattled confidence")],
        )

    return EventScenario(
        title="Wandering Cartographer",
        intro="A lone guide offers rough maps and sparring lessons between travels.",
        biome_keys=None,
        options=[
            EventOption("Trade routes", "Swap a spare item for reliable scouting.", "trade", trade_routes),
            EventOption("Spar for tips", "Spend stamina to test yourself and learn.", "balanced", spar_for_tips),
        ],
    )


SCENARIOS: List[EventScenario] = [
    ruins_archive(),
    wetlands_shrine(),
    cavern_echoes(),
    wandering_cartographer(),
]


def resolve_event(game: "Game", location: "Location", rng: random.Random) -> EventScenario:
    """Select an event scenario appropriate to the biome."""

    candidates: List[EventScenario] = []
    for scenario in SCENARIOS:
        if scenario.biome_keys is None or location.biome.key in scenario.biome_keys:
            candidates.append(scenario)
    if not candidates:
        candidates = SCENARIOS
    return rng.choice(candidates)
