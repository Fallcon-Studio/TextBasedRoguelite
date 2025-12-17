"""Procedural world generation utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence
import random


@dataclass
class Exit:
    """A directed connection from one location to another."""

    destination: str
    label: str
    cost: int
    note: str = ""


@dataclass
class BiomeTemplate:
    """Template data that shapes a location's flavor and rewards."""

    key: str
    title: str
    flavors: List[str]
    encounter_weights: Dict[str, float]
    reward_multiplier: float
    travel_cost: int


@dataclass
class Location:
    """A logical location in the world graph."""

    id: str
    name: str
    biome: BiomeTemplate
    danger: int
    encounter: str  # enemy, rest, event
    description: str
    reward_multiplier: float
    exits: List[Exit] = field(default_factory=list)
    decay_stage: str = "Fresh"
    decay_duration: int = 0
    removed: bool = False


@dataclass
class WorldGraph:
    """The connected structure for a single expedition."""

    nodes: Dict[str, Location]
    start: str


@dataclass
class FrontierModifier:
    """Represents a single modifier contributing to the frontier size."""

    label: str
    value: int


@dataclass
class FrontierSize:
    """Calculation details for the frontier size."""

    base: int = 4
    positive: List[FrontierModifier] = field(default_factory=list)
    negative: List[FrontierModifier] = field(default_factory=list)
    minimum: int = 1
    maximum: int = 7

    def total(self) -> int:
        return self.base + self.positive_total() - self.negative_total()

    def clamped(self) -> int:
        return max(self.minimum, min(self.maximum, self.total()))

    def positive_total(self) -> int:
        return sum(mod.value for mod in self.positive)

    def negative_total(self) -> int:
        return sum(mod.value for mod in self.negative)


@dataclass
class FrontierOption:
    """A single entry in the frontier list."""

    exit: Exit
    location: Location | None
    placeholder: bool = False
    reason: str = ""


@dataclass
class FrontierState:
    """Stable data for the frontier while the player chooses."""

    options: List[FrontierOption]
    size: FrontierSize
    source_location_id: str


BIOMES = [
    BiomeTemplate(
        key="ruins",
        title="Crumbling Ruins",
        flavors=[
            "shattered keeps jagged against a bruised horizon",
            "fallen libraries littered with charred tomes",
            "ivy-choked plazas where statues whisper of old wars",
        ],
        encounter_weights={"enemy": 0.55, "rest": 0.25, "event": 0.2},
        reward_multiplier=1.2,
        travel_cost=1,
    ),
    BiomeTemplate(
        key="wetlands",
        title="Gloomed Wetlands",
        flavors=[
            "silent marshland wrapped in silver mist",
            "sunken causeways riddled with luminous spores",
            "reed-choked canals hiding restless silhouettes",
        ],
        encounter_weights={"enemy": 0.45, "rest": 0.25, "event": 0.3},
        reward_multiplier=1.0,
        travel_cost=2,
    ),
    BiomeTemplate(
        key="caverns",
        title="Hollow Caverns",
        flavors=[
            "fractured caverns buzzing with faint echoes",
            "glimmering basalt passages warmed by hidden vents",
            "crystal hollows that drink in every sound",
        ],
        encounter_weights={"enemy": 0.4, "rest": 0.15, "event": 0.45},
        reward_multiplier=1.35,
        travel_cost=1,
    ),
]


ENCOUNTERS = ["enemy", "rest", "event"]


def _pick_biome(rng: random.Random) -> BiomeTemplate:
    weights = [0.4, 0.35, 0.25]
    return rng.choices(BIOMES, weights=weights, k=1)[0]


def _build_location(rng: random.Random, idx: int) -> Location:
    biome = _pick_biome(rng)
    encounter = rng.choices(
        ENCOUNTERS,
        weights=[
            biome.encounter_weights["enemy"],
            biome.encounter_weights["rest"],
            biome.encounter_weights["event"],
        ],
        k=1,
    )[0]
    danger = rng.randint(1, 3) + idx // 2
    flavor = rng.choice(biome.flavors)
    name = f"{rng.choice(['Forsaken', 'Shaded', 'Broken', 'Forgotten', 'Hidden'])} {biome.title}"
    description = f"You reach {flavor}. Threat level {danger}."
    reward_multiplier = biome.reward_multiplier + (0.05 * (danger - 1))
    return Location(
        id=f"loc-{idx}",
        name=name,
        biome=biome,
        danger=danger,
        encounter=encounter,
        description=description,
        reward_multiplier=reward_multiplier,
    )


def _connect_locations(rng: random.Random, nodes: List[Location]) -> None:
    last_camp: str | None = None
    for idx, location in enumerate(nodes):
        if location.encounter == "rest":
            last_camp = location.id

        if idx == len(nodes) - 1:
            continue

        forward_choices = rng.randint(1, 2)
        potential_targets = list(range(idx + 1, min(len(nodes), idx + 3)))
        rng.shuffle(potential_targets)
        chosen_targets = potential_targets[:forward_choices]

        for position, target_idx in enumerate(chosen_targets):
            target = nodes[target_idx]
            label = ["veer left", "take the high path", "press on"]
            cost = max(1, target.biome.travel_cost + rng.randint(0, 1))
            note = f"toward {target.biome.title.lower()}"
            location.exits.append(
                Exit(
                    destination=target.id,
                    label=label[position % len(label)],
                    cost=cost,
                    note=note,
                )
            )

        if last_camp and last_camp != location.id:
            location.exits.append(
                Exit(
                    destination=last_camp,
                    label="double back to camp",
                    cost=max(1, location.biome.travel_cost),
                    note="safer footing for a breather",
                )
            )


def generate_world(seed: int | None, steps: int) -> WorldGraph:
    """Generate a branching graph of locations for the run."""

    rng = random.Random(seed)
    nodes: List[Location] = []
    capped_steps = max(3, steps)
    for idx in range(capped_steps):
        nodes.append(_build_location(rng, idx))

    _connect_locations(rng, nodes)

    node_map = {loc.id: loc for loc in nodes}
    return WorldGraph(nodes=node_map, start=nodes[0].id)


def _biome_frontier_modifier(
    biome: BiomeTemplate,
) -> tuple[FrontierModifier, bool] | None:
    mapping: Dict[str, tuple[str, int, bool]] = {
        "caverns": ("cavern echoes guide branching paths", 1, True),
        "wetlands": ("bogged trails narrow options", 1, False),
    }
    raw = mapping.get(biome.key)
    if raw is None:
        return None
    label, value, positive = raw
    return FrontierModifier(label, value), positive


def compute_frontier_size(
    player_awareness: int,
    frontier_locations: Sequence[Location],
    *,
    extra_positive: Sequence[FrontierModifier] | None = None,
    extra_negative: Sequence[FrontierModifier] | None = None,
) -> FrontierSize:
    size = FrontierSize()
    awareness_bonus = player_awareness // 5
    if awareness_bonus:
        size.positive.append(
            FrontierModifier(
                label="awareness scouting bonus", value=awareness_bonus
            )
        )

    for location in frontier_locations:
        modifier = _biome_frontier_modifier(location.biome)
        if modifier:
            mod, positive = modifier
            if positive:
                size.positive.append(mod)
            else:
                size.negative.append(mod)

    if extra_positive:
        size.positive.extend(extra_positive)
    if extra_negative:
        size.negative.extend(extra_negative)

    total = size.total()
    if total < size.minimum:
        size.positive.append(
            FrontierModifier("frontier floor guardrail", size.minimum - total)
        )
    if total > size.maximum:
        size.negative.append(
            FrontierModifier("frontier cap guardrail", total - size.maximum)
        )

    return size


def build_frontier_state(
    current: Location,
    world: WorldGraph,
    player_awareness: int,
    *,
    rng: random.Random | None = None,
    extra_positive: Sequence[FrontierModifier] | None = None,
    extra_negative: Sequence[FrontierModifier] | None = None,
) -> FrontierState:
    rng = rng or random.Random()
    candidate_exits = [
        exit
        for exit in current.exits
        if not world.nodes[exit.destination].removed
    ]
    sorted_exits = sorted(candidate_exits, key=lambda ex: ex.destination)
    candidate_locations = [world.nodes[ex.destination] for ex in sorted_exits]

    size = compute_frontier_size(
        player_awareness,
        candidate_locations,
        extra_positive=extra_positive,
        extra_negative=extra_negative,
    )
    target_size = size.clamped()
    working_rng = random.Random((rng or random).random())
    if len(sorted_exits) > target_size:
        working_rng.shuffle(sorted_exits)
    chosen_exits = sorted_exits[:target_size]

    options = [
        FrontierOption(exit=exit, location=world.nodes[exit.destination])
        for exit in chosen_exits
    ]

    if not options:
        placeholder = FrontierOption(
            exit=Exit(
                destination=current.id,
                label="Hold position for the Gatekeeper",
                cost=0,
                note="placeholder until Gatekeeper/exit flow is active",
            ),
            location=None,
            placeholder=True,
            reason="No viable exits; awaiting Gatekeeper placeholder.",
        )
        options.append(placeholder)

    return FrontierState(options=options, size=size, source_location_id=current.id)
