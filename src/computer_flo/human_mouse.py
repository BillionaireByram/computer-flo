from __future__ import annotations

import math
import random
from dataclasses import dataclass

MAX_COORD = 32768


@dataclass(frozen=True)
class HumanPathOptions:
    """OpenHuman-inspired cursor movement profile.

    Generates curved Bezier waypoints with small dwell times so mouse movement
    can be smooth/human-like instead of instant coordinate teleports.
    """

    steps: int = 25
    mean_step_ms: float = 12.0
    stddev_step_ms: float = 4.0
    curvature: float = 0.3


def clamp_coord(value: int) -> int:
    return max(0, min(MAX_COORD, int(value)))


def validate_coord(name: str, value: int) -> None:
    if not 0 <= int(value) <= MAX_COORD:
        raise ValueError(f"{name} coordinate {value} is out of range (0..{MAX_COORD})")


def human_path(
    start: tuple[int, int],
    end: tuple[int, int],
    opts: HumanPathOptions | None = None,
    rng: random.Random | None = None,
) -> list[tuple[int, int, int]]:
    """Return (x, y, dwell_ms) waypoints from start to end."""

    opts = opts or HumanPathOptions()
    rng = rng or random.Random()
    if start == end or opts.steps <= 0:
        return [(clamp_coord(end[0]), clamp_coord(end[1]), 0)]

    sx, sy = float(start[0]), float(start[1])
    ex, ey = float(end[0]), float(end[1])
    dx, dy = ex - sx, ey - sy
    dist = math.hypot(dx, dy)
    if dist == 0:
        return [(clamp_coord(end[0]), clamp_coord(end[1]), 0)]

    steps = min(opts.steps, 3) if dist < 5 else opts.steps
    perp = (-dy / dist, dx / dist)
    deviation = max(0.0, opts.curvature) * dist

    def lerp(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    def offset(point: tuple[float, float], amount: float) -> tuple[float, float]:
        return (point[0] + perp[0] * amount, point[1] + perp[1] * amount)

    p0 = (sx, sy)
    p3 = (ex, ey)
    p1 = offset(lerp(p0, p3, 0.33), rng.gauss(0.0, deviation) if deviation else 0.0)
    p2 = offset(lerp(p0, p3, 0.66), rng.gauss(0.0, deviation) if deviation else 0.0)

    def bezier(t: float) -> tuple[float, float]:
        omt = 1.0 - t
        a = omt**3
        b = 3.0 * omt**2 * t
        c = 3.0 * omt * t**2
        d = t**3
        return (
            a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1],
        )

    path: list[tuple[int, int, int]] = []
    for step in range(steps + 1):
        t = step / steps
        x, y = bezier(t)
        dwell = _dwell_ms(opts, rng)
        path.append((clamp_coord(round(x)), clamp_coord(round(y)), dwell))
    return path


def _dwell_ms(opts: HumanPathOptions, rng: random.Random) -> int:
    mean = opts.mean_step_ms if math.isfinite(opts.mean_step_ms) else HumanPathOptions().mean_step_ms
    stddev = opts.stddev_step_ms if math.isfinite(opts.stddev_step_ms) else HumanPathOptions().stddev_step_ms
    stddev = max(0.0, stddev)
    sample = mean if stddev == 0 else rng.gauss(mean, stddev)
    sample = max(mean - 3.0 * stddev, min(mean + 3.0 * stddev, sample))
    return max(1, round(sample))
