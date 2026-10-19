"""The 1.4.1 furnishing tools, against a fake bridge that records what is sent.

Lines walls, seats tables, dresses surfaces, files placements into groups,
lights objects as they are placed, keeps scatter off walls, aims screenshots,
draws previews to one scale, collapses variants and accepts intentional lights.
"""

from __future__ import annotations

import pytest

from battlemap_mcp import groups, server
from battlemap_mcp.errors import BridgeCommandError, ValidationError

SHELF = "res://packs/P1/textures/objects/bookcase_01.png"
CHAIR = "res://packs/P1/textures/objects/chair_1a.png"
BOOK = "res://packs/P1/textures/objects/book_1a.png"
WALL = "res://packs/P1/textures/walls/stone8a.png"

SIZES = {SHELF: [500, 140], CHAIR: [160, 200], BOOK: [80, 100], WALL: [1024, 100]}


class Bridge:
    """Answers the handful of commands the tools compose from, and logs every call."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.walls = [
            {
                "id": 1,
                "kind": "wall",
                "asset": WALL,
                "loop": True,
                "points": [[0, 0], [2048, 0], [2048, 2048], [0, 2048]],
            }
        ]
        self.portals = [{"id": 2, "position": [1024, 0], "radius": 128, "wall_id": 1}]
        self.objects: list[dict] = []
        self.elements: dict[int, dict] = {}
        self.next_id = 100

    def __call__(self, command, **params):
        self.calls.append((command, params))
        if command == "list_elements":
            kind = params["kind"]
            items = {"walls": self.walls, "portals": self.portals, "objects": self.objects}.get(
                kind, []
            )
            return {"elements": items, "total": len(items)}
        if command == "list_assets":
            wanted = list(params.get("only", []))
            return {"assets": wanted, "sizes": [SIZES.get(a) for a in wanted], "colorable": []}
        if command == "get_element":
            ident = params["id"]
            if ident not in self.elements:
                raise BridgeCommandError(f"no element with id {ident}", cmd=command)
            return self.elements[ident]
        if command == "place_objects":
            out = []
            for entry in params["objects"]:
                record = {"id": self.next_id, "position": [entry.get("x"), entry.get("y")]}
                self.elements[self.next_id] = {"kind": "object", **entry}
                self.next_id += 1
                if "light" in entry:
                    record["light_id"] = self.next_id
                    self.elements[self.next_id] = {"kind": "light"}
                    self.next_id += 1
                out.append(record)
            return {"placed": len(out), "objects": out, "ids": [o["id"] for o in out]}
        if command == "add_lights":
            ids = list(range(self.next_id, self.next_id + len(params["lights"])))
            self.next_id += len(ids)
            for ident in ids:
                self.elements[ident] = {"kind": "light"}
            return {"added": len(ids), "ids": ids}
        if command in ("delete_elements", "fit_elements", "move_elements", "set_camera"):
            return {"ok": True, **params}
        if command == "get_camera":
            return {"viewport_size": [1600, 900]}
        if command == "modify_light":
            return {"kind": "light", "range": params.get("range", 1.0), "id": params["id"]}
        if command == "scatter_objects":
            return {"placed": 1, "ids": [self.next_id]}
        if command == "add_light":
            self.elements[self.next_id] = {"kind": "light"}
            self.next_id += 1
            return {"id": self.next_id - 1}
        return {}

    def sent(self, command):
        return [params for name, params in self.calls if name == command]


@pytest.fixture
def bridge(monkeypatch):
    fake = Bridge()
    monkeypatch.setattr(server.bridge, "request", fake)
    return fake


# --- place_along_wall -------------------------------------------------------------


def test_a_wall_run_is_flush_faces_the_room_and_clears_the_door(bridge):
    result = server.place_along_wall([0, 0], [2048, 0], [1024, 1024], [SHELF])
    assert result["wall_id"] == 1 and result["thickness"] == 100.0 and result["rotation"] == 0.0
    assert result["free_stretches"] == [[74, 872], [1176, 1974]]
    placed = bridge.sent("place_objects")[0]["objects"]
    assert [(e["x"], e["y"], e["rotation"]) for e in placed] == [
        (473.0, 120.0, 0.0),
        (1575.0, 120.0, 0.0),
    ]
    assert result["ids"] == [100, 101]


def test_a_wall_run_stops_short_of_an_object_already_there(bridge):
    bridge.objects = [{"id": 9, "layer": 100, "bounds": [1300, 60, 1500, 200]}]
    server.place_along_wall([0, 0], [2048, 0], [1024, 1024], [SHELF])
    xs = [e["x"] for e in bridge.sent("place_objects")[0]["objects"]]
    assert len(xs) == 1 and xs[0] < 872  # the right-hand stretch is now too short


def test_a_rug_under_the_run_does_not_count_as_taken(bridge):
    bridge.objects = [{"id": 9, "layer": 0, "bounds": [100, 60, 1900, 600]}]
    server.place_along_wall([0, 0], [2048, 0], [1024, 1024], [SHELF])
    assert len(bridge.sent("place_objects")[0]["objects"]) == 2


def test_an_east_wall_run_turns_to_face_west(bridge):
    result = server.place_along_wall([2048, 0], [2048, 2048], [1024, 1024], [SHELF], dry_run=True)
    assert result["rotation"] == 90.0
    assert {e["x"] for e in result["planned"]} == {2048 - 50 - 70}
    assert not bridge.sent("place_objects")


def test_a_stretch_off_every_wall_is_refused(bridge):
    with pytest.raises(ValidationError, match="does not run along any wall"):
        server.place_along_wall([500, 900], [1500, 900], [1000, 1200], [SHELF])


# --- seat_around and dress_surface --------------------------------------------------


def test_seats_are_derived_from_the_placed_table(bridge):
    bridge.elements[7] = {
        "kind": "object",
        "position": [1000, 1000],
        "rotation": 0.0,
        "scale": 1.0,
        "texture_size": [600, 300],
        "layer": 100,
    }
    result = server.seat_around(7, [CHAIR], per_side=2, jitter=0, group="dining")
    chairs = bridge.sent("place_objects")[0]["objects"]
    assert result["chairs"] == 4 and len(chairs) == 4
    assert sorted({c["rotation"] for c in chairs}) == [0.0, 180.0]
    assert {c["layer"] for c in chairs} == {100}
    assert server.list_groups("dining")["ids"] == result["ids"]


def test_dressing_goes_one_layer_up_and_reports_what_did_not_fit(bridge):
    bridge.elements[8] = {
        "kind": "object",
        "position": [500, 500],
        "rotation": 90.0,
        "scale": 1.0,
        "texture_size": [475, 301],
        "layer": 100,
    }
    result = server.dress_surface(8, [BOOK], count=40, seed=2)
    placed = bridge.sent("place_objects")[0]["objects"]
    assert {p["layer"] for p in placed} == {200}
    assert result["items"] == len(placed) and result["not_fitted"] == 40 - len(placed)
    assert "did not fit" in result["fit_note"]


def test_a_tool_on_a_bridge_without_sizes_says_what_to_update(monkeypatch, bridge):
    def no_sizes(command, **params):
        if command == "list_assets":
            return {"assets": params.get("only", []), "colorable": []}
        return bridge(command, **params)

    monkeypatch.setattr(server.bridge, "request", no_sizes)
    bridge.elements[8] = {"kind": "object", "position": [0, 0], "texture_size": [400, 300]}
    with pytest.raises(ValidationError, match="restart Dungeondraft"):
        server.dress_surface(8, [BOOK])


# --- groups -------------------------------------------------------------------------


def test_a_group_collects_objects_and_their_lights_and_deletes_together(bridge):
    server.place_objects(
        [
            server.PlacedObject(asset=BOOK, x=10, y=10, light=server.LightSpec(range=3)),
            server.PlacedObject(asset=BOOK, x=20, y=20),
        ],
        group="hall/tables",
    )
    ids = server.list_groups("hall/tables")["ids"]
    assert sorted(ids) == [100, 101, 102]
    light_sent = bridge.sent("place_objects")[0]["objects"][0]["light"]
    assert light_sent["range"] == 1.5  # editor range 3 is texture_scale 1.5
    del bridge.elements[102]  # gone some other way
    server.delete_elements(group="hall/tables")
    assert bridge.sent("delete_elements")[-1]["ids"] == [100, 101]


def test_group_names_are_checked_before_anything_is_placed(bridge):
    with pytest.raises(ValidationError, match="not a usable name"):
        server.place_objects([server.PlacedObject(asset=BOOK)], group="  ")
    with pytest.raises(ValidationError, match="not a usable name"):
        server.place_object(BOOK, group="bad|name")
    assert not bridge.sent("place_objects") and not bridge.sent("place_object")


def test_an_unknown_group_is_refused_with_the_known_ones(bridge):
    groups.add("north wall", [1])
    with pytest.raises(ValidationError, match="north wall"):
        server.fit_elements(group="south wall")
    with pytest.raises(ValidationError, match="ids or group"):
        server.move_elements(ids=[1], group="north wall", dx=10)


# --- lights -------------------------------------------------------------------------


def test_place_object_with_a_light_goes_through_one_batch(bridge):
    result = server.place_object(BOOK, x=5, y=5, light=server.LightSpec(color="#ffaa00"))
    assert result["light_id"] == 101
    assert not bridge.sent("place_object")
    assert bridge.sent("place_objects")[0]["objects"][0]["light"]["color"] == "#ffaa00"


def test_add_lights_converts_range_and_remembers_intentional_ones(bridge):
    result = server.add_lights(
        [
            server.LightEntry(x=1, y=2, range=4),
            server.LightEntry(x=3, y=4, intentional="moonlight through the window"),
        ],
        group="lights",
    )
    sent = bridge.sent("add_lights")[0]["lights"]
    assert [entry["range"] for entry in sent] == [2.0, 1.0]
    assert server._INTENTIONAL_LIGHTS == {result["ids"][1]: "moonlight through the window"}
    assert server.list_groups("lights")["ids"] == result["ids"]


def test_modify_light_sends_only_what_changes_in_bridge_units(bridge):
    result = server.modify_light(42, range=6)
    assert bridge.sent("modify_light") == [{"id": 42, "range": 3.0}]
    assert result["range"] == 6.0
    with pytest.raises(ValidationError):
        server.modify_light(42)


# --- scatter, screenshots, previews, variants ---------------------------------------


def test_scatter_passes_its_keep_out_zones(bridge):
    server.scatter_objects([BOOK], [0, 0, 500, 500], wall_margin=0, avoid_rects=[[10, 10, 50, 50]])
    sent = bridge.sent("scatter_objects")[0]
    assert sent["wall_margin"] == 0 and sent["avoid_rects"] == [[10, 10, 50, 50]]
    with pytest.raises(ValidationError):
        server.scatter_objects([BOOK], [0, 0, 500, 500], wall_margin=-1)


def test_aiming_fits_a_rect_or_a_tile_count(bridge):
    server._aim([0, 0, 3200, 900], None, None)
    view = bridge.sent("set_camera")[-1]
    assert (view["x"], view["y"]) == (1600, 450)
    assert view["zoom"] == pytest.approx(2.0 * server.AIM_PAD)
    server._aim(None, [100, 200], 12.5)
    assert bridge.sent("set_camera")[-1]["zoom"] == pytest.approx(12.5 * 256 / 1600)
    with pytest.raises(ValidationError):
        server._aim([0, 0, 10, 10], [0, 0], 4)


def test_a_true_scale_caption_says_what_a_cell_spans():
    caption = server._preview_caption(
        [BOOK], {"true_scale": True, "woxels_per_cell": 1024.0, "sizes": {}, "missing": []}
    )
    assert caption.startswith("True scale: every cell spans 1024 woxels (4.0 tiles).")


def test_colour_variants_collapse_into_one_entry(monkeypatch):
    listing = {
        "assets": [
            "res://p/book_1a.png",
            "res://p/book_1b.png",
            "res://p/bookcase_01.png",
            "res://p/bookcase_03.png",
            "res://p/book_1x.png",
        ],
        "sizes": [[1, 1], [2, 2], [3, 3], [4, 4], [5, 5]],
        "colorable": [4],
    }
    monkeypatch.setattr(server.bridge, "request", lambda command, **params: listing)
    result = server.list_assets("Objects", "book", group_variants=True)
    assert result["assets"] == [
        "res://p/book_1a.png",
        "res://p/bookcase_01.png",
        "res://p/bookcase_03.png",
    ]
    assert result["variants"] == {"0": ["res://p/book_1b.png", "res://p/book_1x.png"]}
    assert result["sizes"] == [[1, 1], [3, 3], [4, 4]]
    assert result["colorable"] == []


def test_validate_scene_credits_an_intentional_light():
    from battlemap_mcp.scene import find_unexplained_lights

    lights = [{"id": 5, "position": [0, 0]}, {"id": 6, "position": [900, 900]}]
    found = find_unexplained_lights(lights, [], intentional={5: "moonlight"})
    assert found["explained"][0]["by"] == "intentional: moonlight"
    assert [entry["id"] for entry in found["unexplained"]] == [6]
