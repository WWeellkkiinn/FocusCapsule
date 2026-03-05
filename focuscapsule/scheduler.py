from __future__ import annotations

import random


def build_trigger_points(
    total_sec: int,
    min_interval_sec: int,
    max_interval_sec: int,
    guard_tail_sec: int,
    seed: int | None = None,
) -> list[int]:
    if total_sec <= 0:
        return []
    if min_interval_sec <= 0 or max_interval_sec <= 0:
        return []
    if min_interval_sec > max_interval_sec:
        return []

    rng = random.Random(seed)
    points: list[int] = []
    remaining = total_sec

    while True:
        step = rng.randint(min_interval_sec, max_interval_sec)
        candidate = remaining - step
        if candidate <= guard_tail_sec:
            break
        if candidate >= total_sec:
            break
        points.append(candidate)
        remaining = candidate

    return sorted(set(points), reverse=True)
