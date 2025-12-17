"""Awareness-driven helpers for frontier sizing and decay visibility."""

from __future__ import annotations

from typing import Literal

FrontierBonus = int
DecayVisibility = Literal["stage", "hint", "exact"]


def frontier_modifier_from_awareness(awareness: int) -> FrontierBonus:
    """Return the frontier-size bonus granted by Awareness.

    Per the rules, every 5 points of Awareness add +1 to the frontier modifier.
    """

    return max(0, awareness // 5)


def decay_visibility_band(awareness: int) -> DecayVisibility:
    """Map Awareness to decay information granularity bands."""

    if awareness >= 10:
        return "exact"
    if awareness >= 5:
        return "hint"
    return "stage"


def format_decay_detail(stage: str, remaining: int, visibility: DecayVisibility) -> str:
    """Format decay information according to the visibility band."""

    if visibility == "stage":
        return stage

    if visibility == "hint":
        if remaining <= 0:
            hint = "shifts immediately"
        elif remaining == 1:
            hint = "about to shift"
        elif remaining <= 2:
            hint = "shifting soon"
        else:
            hint = "holding for a short while"
        return f"{stage} ({hint})"

    timing = "time" if abs(remaining) == 1 else "time"
    return f"{stage} — {max(0, remaining)} {timing} until the next stage"
