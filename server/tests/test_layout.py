"""The furnishing geometry: flush to walls, clear of doors, chairs facing tables."""

from __future__ import annotations

import math

import pytest

from battlemap_mcp import layout


@pytest.mark.parametrize(
    "normal, rotation",
    [((0, 1), 0.0), ((-1, 0), 90.0), ((0, -1), 180.0), ((1, 0), 270.0)],
)
def test_facing_matches_the_wall_table_every_skill_quotes(normal, rotation):
    # North wall faces the room below it: 0. East wall faces west: 90. And so on.
    assert layout.facing_rotation(*normal) == rotation


def test_a_rotated_front_points_where_facing_says():
    for degrees in (0, 37, 90, 211, 270):
        nx, ny = layout.rotate(0, 1, degrees)
        assert layout.facing_rotation(nx, ny) == pytest.approx(degrees % 360, abs=1e-6)


def test_the_room_side_decides_the_normal():
    frame = layout.wall_frame((0, 0), (1000, 0), (500, 400))
    assert frame.normal == (0.0, 1.0)
    frame = layout.wall_frame((0, 0), (1000, 0), (500, -400))
    assert frame.normal == (-0.0, -1.0) or frame.normal == (0.0, -1.0)
    with pytest.raises(ValueError):
        layout.wall_frame((0, 0), (1000, 0), (500, 0))


def test_free_stretches_subtract_every_blocked_interval():
    assert layout.free_stretches(0, 100, [(20, 30), (60, 120)]) == [(0, 20), (30, 60)]
    assert layout.free_stretches(0, 100, []) == [(0, 100)]
    assert layout.free_stretches(0, 100, [(-5, 200)]) == []


def test_a_run_stands_flush_centred_and_clear_of_a_door():
    frame = layout.wall_frame((0, 0), (2048, 0), (1024, 1024))
    spots, stretches = layout.wall_run(
        frame,
        74,
        1974,
        thickness=100,
        sizes=[(500, 140)],
        blocked=[(872, 1176)],
    )
    assert stretches == [(74, 872), (1176, 1974)]
    assert [(s.x, s.y, s.rotation) for s in spots] == [(473.0, 120.0, 0.0), (1575.0, 120.0, 0.0)]


def test_a_run_alternates_assets_and_never_overfills():
    frame = layout.wall_frame((0, 0), (0, 1000), (500, 500))  # west wall, room to the east
    spots, _ = layout.wall_run(frame, 0, 1000, thickness=0, sizes=[(300, 100), (200, 100)])
    assert [s.index for s in spots] == [0, 1, 0, 1]
    assert {s.rotation for s in spots} == {270.0}
    assert all(s.x == 50.0 for s in spots)
    # 300+200+300+200 = 1000 exactly fills it; a fifth piece would not fit.
    assert len(spots) == 4


def test_spacing_and_gap_are_honoured():
    frame = layout.wall_frame((0, 0), (1000, 0), (0, 500))
    spots, _ = layout.wall_run(
        frame, 0, 1000, thickness=50, sizes=[(200, 100)], spacing=100, gap=10
    )
    # 3 pieces need 3*200 + 2*100 = 800; a fourth would need 1100.
    assert len(spots) == 3
    assert spots[1].x - spots[0].x == pytest.approx(300)
    assert spots[0].y == pytest.approx(25 + 10 + 50)


def test_chairs_line_the_long_sides_and_face_the_table():
    spots = layout.seats_around((1000, 1000), 0.0, (600, 300), (160, 200), per_side=2, jitter=0)
    assert len(spots) == 4
    above = sorted((s for s in spots if s.y < 1000), key=lambda s: s.x)
    below = [s for s in spots if s.y > 1000]
    assert [s.x for s in sorted(above, key=lambda s: s.x)] == [850.0, 1150.0]
    assert {s.rotation for s in above} == {0.0}
    assert {s.rotation for s in below} == {180.0}
    reach = 150 + 100 - 0.15 * 200
    assert above[0].y == pytest.approx(1000 - reach)


def test_chairs_follow_a_turned_table():
    straight = layout.seats_around((0, 0), 0.0, (600, 300), (160, 200), ends=True, jitter=0)
    turned = layout.seats_around((0, 0), 90.0, (600, 300), (160, 200), ends=True, jitter=0)
    for a, b in zip(straight, turned, strict=True):
        rx, ry = layout.rotate(a.x, a.y, 90)
        assert (b.x, b.y) == pytest.approx((rx, ry), abs=0.05)
        assert b.rotation == pytest.approx((a.rotation + 90) % 360, abs=0.05)


def test_a_round_table_gets_an_even_ring():
    spots = layout.seats_around((0, 0), 0.0, (400, 400), (160, 200), around=4, jitter=0)
    radii = {round(math.hypot(s.x, s.y), 1) for s in spots}
    assert len(spots) == 4 and len(radii) == 1
    assert sorted(s.rotation for s in spots) == [0.0, 90.0, 180.0, 270.0]


def test_items_stay_inside_the_surface_even_when_turned():
    spots, missing = layout.on_surface(
        (500, 500), 30.0, (475, 301), [(80, 100), (170, 126)], 4, seed=3
    )
    assert missing == 0 and len(spots) == 4
    for s in spots:
        lx, ly = layout.rotate(s.x - 500, s.y - 500, -30.0)
        assert abs(lx) < 475 / 2 and abs(ly) < 301 / 2


def test_an_item_too_big_for_the_surface_is_reported_not_hung_over():
    spots, missing = layout.on_surface((0, 0), 0.0, (100, 100), [(300, 300)], 2, seed=1)
    assert spots == [] and missing == 2
