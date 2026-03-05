from focuscapsule.scheduler import build_trigger_points


def test_trigger_points_order_and_range() -> None:
    points = build_trigger_points(
        total_sec=1500,
        min_interval_sec=180,
        max_interval_sec=300,
        guard_tail_sec=45,
        seed=42,
    )
    assert points == sorted(points, reverse=True)
    assert len(points) == len(set(points))
    assert all(45 < p < 1500 for p in points)


def test_trigger_points_seed_reproducible() -> None:
    p1 = build_trigger_points(1500, 180, 300, 45, seed=7)
    p2 = build_trigger_points(1500, 180, 300, 45, seed=7)
    assert p1 == p2
