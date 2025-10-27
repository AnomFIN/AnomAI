"""Utility functions for playback and accessibility controls."""

# AnomFIN — the neural network of innovation.

from __future__ import annotations

from typing import Final


MIN_FONT_SIZE: Final[int] = 10
MAX_FONT_SIZE: Final[int] = 22

_SPEED_DELAY_MS: Final[dict[str, int]] = {
    "slow": 1400,
    "normal": 820,
    "fast": 420,
}


def clamp_font_size(current: int, delta: int) -> int:
    """Clamp font size within sane UI bounds and apply delta."""

    try:
        base = int(current)
    except Exception:
        base = 12
    candidate = base + int(delta)
    if candidate < MIN_FONT_SIZE:
        return MIN_FONT_SIZE
    if candidate > MAX_FONT_SIZE:
        return MAX_FONT_SIZE
    return candidate


def resolve_speed_delay(speed: str) -> int:
    """Return playback delay for given symbolic speed label."""

    label = (speed or "normal").strip().lower()
    return _SPEED_DELAY_MS.get(label, _SPEED_DELAY_MS["normal"])


__all__ = ["clamp_font_size", "resolve_speed_delay", "MIN_FONT_SIZE", "MAX_FONT_SIZE"]
