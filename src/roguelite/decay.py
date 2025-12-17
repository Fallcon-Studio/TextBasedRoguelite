"""Track world decay and time passage for frontier locations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List
import random

from .world import Location, WorldGraph


DECAY_STAGES = ["Fresh", "Fading", "Withering", "Removed"]


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

    def initialize_locations(self, locations: Dict[str, Location]) -> None:
        """Seed decay states for all locations in the run."""

        for location in locations.values():
            duration = self.rng.randint(2, 4)
            state = DecayState(stage_index=0, remaining=duration, duration=duration)
            self.state[location.id] = state
            self._sync_location(location, state)

    def _sync_location(self, location: Location, state: DecayState) -> None:
        location.decay_stage = DECAY_STAGES[state.stage_index]
        location.decay_duration = state.duration
        location.removed = state.stage_index >= len(DECAY_STAGES) - 1

    def advance_frontier(
        self, time_spent: int, world: WorldGraph, frontier_ids: Iterable[str]
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
                state.remaining += state.duration

            location = world.nodes[loc_id]
            self._sync_location(location, state)
            if state.stage_index >= len(DECAY_STAGES) - 1:
                removed.append(loc_id)

        return removed
