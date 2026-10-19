"""Where furniture goes: along a wall, around a table, on a surface.

A library build computed all of this by hand in throwaway scripts: the offset
that puts a bookcase flush against a wall of a given thickness, the rotation
that turns its books to the room, the gaps a door and a window need, the corner
where two runs of shelving collide, the chair spacing that matches a table's
real length, the book scale that fits on a desk. Each was a source of a visible
mistake at least once.

These are pure functions over numbers, so the rules are tested here without a
running editor; server.py reads the map, calls them, and places the result.

Conventions: woxels, y grows DOWN, rotation in degrees clockwise. Dungeondraft
draws a fixture facing DOWN at rotation 0 — its front at the bottom of the
sprite, its back at the top — so "facing" a direction means turning that front
toward it.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

Point = tuple[float, float]


@dataclass(frozen=True)
class Placement:
    """One object to place: which candidate asset, where, and how turned."""

    index: int
    x: float
    y: float
    rotation: float


def facing_rotation(nx: float, ny: float) -> float:
    """The rotation that turns a down-facing sprite's front toward (nx, ny).

    Down (0, 1) is 0, west (-1, 0) is 90, up is 180, east is 270: a bookcase
    against an east wall faces west and takes 90, the table every skill quotes.
    """
    degrees = math.degrees(math.atan2(-nx, ny)) % 360.0
    return 0.0 if math.isclose(degrees, 360.0) or abs(degrees) < 1e-9 else round(degrees, 4)


def rotate(x: float, y: float, degrees: float) -> Point:
    """A vector turned clockwise on screen (y down) by `degrees`."""
    radians = math.radians(degrees)
    c, s = math.cos(radians), math.sin(radians)
    return (x * c - y * s, x * s + y * c)


# --- along a wall -------------------------------------------------------------


@dataclass(frozen=True)
class WallFrame:
    """A wall segment as a line: origin, unit direction, unit normal to the room."""

    a: Point
    direction: Point
    normal: Point
    length: float

    def at(self, t: float, offset: float) -> Point:
        return (
            self.a[0] + self.direction[0] * t + self.normal[0] * offset,
            self.a[1] + self.direction[1] * t + self.normal[1] * offset,
        )

    def along(self, point: Point) -> float:
        return (point[0] - self.a[0]) * self.direction[0] + (point[1] - self.a[1]) * self.direction[
            1
        ]

    def across(self, point: Point) -> float:
        return (point[0] - self.a[0]) * self.normal[0] + (point[1] - self.a[1]) * self.normal[1]


def wall_frame(a: Point, b: Point, toward: Point) -> WallFrame:
    """The segment a->b with its normal turned to the side `toward` is on."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 1e-6:
        raise ValueError("the wall segment has no length")
    direction = (dx / length, dy / length)
    normal = (-direction[1], direction[0])
    side = (toward[0] - a[0]) * normal[0] + (toward[1] - a[1]) * normal[1]
    if abs(side) < 1e-6:
        raise ValueError("`toward` lies on the wall line, so it names neither side")
    if side < 0:
        normal = (-normal[0], -normal[1])
    return WallFrame(a, direction, normal, length)


def distance_to_segment(p: Point, a: Point, b: Point) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    if length2 < 1e-12:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length2))
    return math.hypot(p[0] - (a[0] + dx * t), p[1] - (a[1] + dy * t))


def free_stretches(
    start: float, end: float, blocked: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    """[start, end] minus every blocked interval, in order."""
    pieces = [(start, end)]
    for low, high in sorted(blocked):
        nxt = []
        for s, e in pieces:
            if high <= s or low >= e:
                nxt.append((s, e))
                continue
            if low > s:
                nxt.append((s, low))
            if high < e:
                nxt.append((high, e))
        pieces = nxt
    return [(s, e) for s, e in pieces if e - s > 1e-6]


def wall_run(
    frame: WallFrame,
    start: float,
    end: float,
    *,
    thickness: float,
    sizes: list[tuple[float, float]],
    scale: float = 1.0,
    spacing: float = 0.0,
    gap: float = 0.0,
    blocked: list[tuple[float, float]] | None = None,
) -> tuple[list[Placement], list[tuple[float, float]]]:
    """Pieces in a row along a wall, backs to it, centred in each free stretch.

    sizes: each candidate's [width, depth] at scale 1, used in turn; the width
    runs along the wall. Pieces stand `thickness/2 + gap` off the wall line, so
    with gap 0 their backs touch its face. A stretch too short for the next
    piece is left empty rather than overfilled. Returns the placements and the
    free stretches it filled.
    """
    if not sizes:
        raise ValueError("no sizes to place")
    rotation = facing_rotation(*frame.normal)
    stretches = free_stretches(start, end, blocked or [])
    placements: list[Placement] = []
    turn = 0
    for low, high in stretches:
        room = high - low
        chosen: list[int] = []
        used = 0.0
        while True:
            index = (turn + len(chosen)) % len(sizes)
            width = sizes[index][0] * scale
            need = width + (spacing if chosen else 0.0)
            if used + need > room + 1e-6:
                break
            chosen.append(index)
            used += need
        if not chosen:
            continue
        turn += len(chosen)
        cursor = low + (room - used) / 2.0
        for position, index in enumerate(chosen):
            width, depth = sizes[index][0] * scale, sizes[index][1] * scale
            if position:
                cursor += spacing
            centre = cursor + width / 2.0
            cursor += width
            x, y = frame.at(centre, thickness / 2.0 + gap + depth / 2.0)
            placements.append(Placement(index, round(x, 2), round(y, 2), rotation))
    return placements, stretches


# --- around a table -------------------------------------------------------------


def seats_around(
    centre: Point,
    rotation: float,
    table_size: tuple[float, float],
    chair_size: tuple[float, float],
    *,
    per_side: int = 2,
    ends: bool = False,
    around: int = 0,
    tuck: float = 0.15,
    jitter: float = 2.0,
    seed: int | None = None,
) -> list[Placement]:
    """Chairs facing a table, spaced from its real edges, one scale for all.

    table_size and chair_size are already scaled: [width, height] of each as
    drawn. The long sides get `per_side` chairs each, evenly spaced; `ends` adds
    one at each short end; `around` > 0 instead rings that many evenly around a
    round table. `tuck` pushes each chair that fraction of its depth under the
    table edge, as chairs drawn up to a table stand. jitter: at most this many
    degrees of turn per chair, so a set is even but not stamped.
    """
    rng = random.Random(seed)
    width, height = table_size
    depth = chair_size[1]
    reach = depth / 2.0 - tuck * depth
    long_axis_x = width >= height
    half_long = (width if long_axis_x else height) / 2.0
    half_short = (height if long_axis_x else width) / 2.0
    local: list[tuple[float, float, float, float]] = []  # x, y, face_x, face_y

    if around > 0:
        radius = max(width, height) / 2.0 + reach
        for k in range(around):
            angle = 2.0 * math.pi * k / around
            ux, uy = math.sin(angle), -math.cos(angle)
            local.append((ux * radius, uy * radius, -ux, -uy))
    else:
        for i in range(per_side):
            along = -half_long + 2.0 * half_long * (i + 0.5) / per_side
            for side in (-1.0, 1.0):
                off = side * (half_short + reach)
                if long_axis_x:
                    local.append((along, off, 0.0, -side))
                else:
                    local.append((off, along, -side, 0.0))
        if ends:
            for side in (-1.0, 1.0):
                off = side * (half_long + reach)
                if long_axis_x:
                    local.append((off, 0.0, -side, 0.0))
                else:
                    local.append((0.0, off, 0.0, -side))

    placements = []
    for lx, ly, fx, fy in local:
        wx, wy = rotate(lx, ly, rotation)
        face = rotate(fx, fy, rotation)
        turn = facing_rotation(*face) + rng.uniform(-jitter, jitter)
        placements.append(
            Placement(0, round(centre[0] + wx, 2), round(centre[1] + wy, 2), round(turn % 360.0, 2))
        )
    return placements


# --- on a surface -------------------------------------------------------------


def on_surface(
    centre: Point,
    rotation: float,
    surface_size: tuple[float, float],
    item_sizes: list[tuple[float, float]],
    count: int,
    *,
    margin: float = 0.08,
    jitter: float = 25.0,
    seed: int | None = None,
    attempts: int = 400,
) -> tuple[list[Placement], int]:
    """Items scattered on a table or desk top, every one wholly inside it.

    item_sizes are already scaled. Each item keeps its whole turned footprint
    (its half diagonal) inside the surface inset by `margin` of the shorter
    side, and items keep apart from each other. Returns the placements and how
    many could not be fitted.
    """
    rng = random.Random(seed)
    width, height = surface_size
    inset = margin * min(width, height)
    half_w, half_h = width / 2.0 - inset, height / 2.0 - inset
    placed: list[tuple[float, float, float]] = []  # local x, y, radius
    out: list[Placement] = []
    tries = 0
    while len(out) < count and tries < attempts:
        tries += 1
        index = rng.randrange(len(item_sizes))
        iw, ih = item_sizes[index]
        radius = math.hypot(iw, ih) / 2.0
        if radius > half_w or radius > half_h:
            continue
        lx = rng.uniform(-half_w + radius, half_w - radius)
        ly = rng.uniform(-half_h + radius, half_h - radius)
        if any(math.hypot(lx - px, ly - py) < 0.75 * (radius + pr) for px, py, pr in placed):
            continue
        placed.append((lx, ly, radius))
        wx, wy = rotate(lx, ly, rotation)
        turn = (rotation + rng.uniform(-jitter, jitter)) % 360.0
        out.append(
            Placement(index, round(centre[0] + wx, 2), round(centre[1] + wy, 2), round(turn, 2))
        )
    return out, count - len(out)
