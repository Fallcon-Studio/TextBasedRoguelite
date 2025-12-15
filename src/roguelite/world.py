"""Procedural world generation utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
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


@dataclass
class WorldGraph:
    """The connected structure for a single expedition."""

    nodes: Dict[str, Location]
    start: str


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
