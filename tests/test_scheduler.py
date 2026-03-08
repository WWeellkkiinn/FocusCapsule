from focuscapsule.scheduler import build_trigger_points


def test_trigger_points_are_ordered_unique_in_range_and_seed_reproducible() -> None:
    points = build_trigger_points(
        total_sec=1500,
        min_interval_sec=180,
        max_interval_sec=300,
        guard_tail_sec=45,
        seed=42,
    )

    assert points == sorted(points, reverse=True)
    assert len(points) == len(set(points))
    assert all(45 < point < 1500 for point in points)
    assert points == build_trigger_points(1500, 180, 300, 45, seed=42)


def test_trigger_points_stop_when_tail_is_shorter_than_min_interval() -> None:
    points = build_trigger_points(
        total_sec=500,
        min_interval_sec=180,
        max_interval_sec=180,
        guard_tail_sec=45,
        seed=1,
    )

    assert points == [320]
