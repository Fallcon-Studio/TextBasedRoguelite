"""Track world decay and time passage for frontier locations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List
import random

from .world import Location, WorldGraph


DECAY_STAGES = ["Fresh", "Fading", "Withering", "Removed"]
DECAY_DURATION_RANGE = (2, 4)


@dataclass
class DecayState:
    """Per-location decay bookkeeping."""

    stage_index: int
    remaining: int
    duration: int


class DecayManager:
    """Controls decay timing for locations ahead of the player."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.time_elapsed: int = 0
        self.state: Dict[str, DecayState] = {}

    def initialize_locations(self, locations: Dict[str, Location], instability: float) -> None:
        """Seed decay states for all locations in the run."""

        for location in locations.values():
            duration = self._roll_decay_duration(instability)
            state = DecayState(stage_index=0, remaining=duration, duration=duration)
            self.state[location.id] = state
            self._sync_location(location, state)

    def _sync_location(self, location: Location, state: DecayState) -> None:
        location.decay_stage = DECAY_STAGES[state.stage_index]
        location.decay_duration = state.duration
        location.decay_remaining = max(0, state.remaining)
        location.removed = state.stage_index >= len(DECAY_STAGES) - 1

    def advance_frontier(
        self,
        time_spent: int,
        world: WorldGraph,
        frontier_ids: Iterable[str],
        instability: float,
    ) -> List[str]:
        """Advance decay for the visible frontier and return removed locations."""

        removed: List[str] = []
        if time_spent <= 0:
            return removed

        self.time_elapsed += time_spent
        for loc_id in frontier_ids:
            if loc_id not in self.state:
                continue
            state = self.state[loc_id]
            if state.stage_index >= len(DECAY_STAGES) - 1:
                continue

            state.remaining -= time_spent
            while state.remaining <= 0 and state.stage_index < len(DECAY_STAGES) - 1:
                state.stage_index += 1
                if state.stage_index >= len(DECAY_STAGES) - 1:
                    break
                new_duration = self._roll_decay_duration(instability)
                state.duration = new_duration
                state.remaining += new_duration

            location = world.nodes[loc_id]
            self._sync_location(location, state)
            if state.stage_index >= len(DECAY_STAGES) - 1:
                removed.append(loc_id)

        return removed

    def _roll_decay_duration(self, instability: float) -> int:
        """Roll a decay duration using instability-weighted extremes and inner values."""

        minimum, maximum = DECAY_DURATION_RANGE
        if maximum <= minimum:
            return minimum

        clamped_instability = max(0.0, min(10.0, instability))
        if clamped_instability < 3:
            extreme_weight, inner_weight = 0, 10
        elif clamped_instability < 6:
            extreme_weight, inner_weight = 4, 6
        elif clamped_instability < 9:
            extreme_weight, inner_weight = 6, 4
        else:
            extreme_weight, inner_weight = 10, 0

        values = list(range(minimum, maximum + 1))
        weights: List[int] = []
        for value in values:
            if value in {minimum, maximum}:
                weights.append(extreme_weight)
            else:
                weights.append(inner_weight)

        if all(weight == 0 for weight in weights):
            weights = [1 for _ in weights]

        return self.rng.choices(values, weights=weights, k=1)[0]
