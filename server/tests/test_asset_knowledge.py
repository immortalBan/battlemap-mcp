"""What a session can know about an asset before placing it.

Sizes, the other names a library uses, which pack to stay inside, and notes an
earlier session left. Each of these replaced a slow discovery in a real build:
test placements to read a texture size, blank searches for `rug` and
`bookshelf`, and a corner bookcase previewed afresh every session.
"""

from __future__ import annotations

import json

import pytest

from battlemap_mcp import asset_notes, asset_vocabulary, server
from battlemap_mcp.errors import ValidationError

CARPET = "res://packs/AbC123/textures/objects/carpet_1a.png"
CARPET_B = "res://packs/AbC123/textures/objects/carpet_2a.png"
SHELF = "res://packs/AbC123/textures/objects/bookcase_1a.png"


# --- vocabulary -------------------------------------------------------------


def test_a_word_swaps_for_the_names_libraries_use_most_specific_first():
    assert asset_vocabulary.alternatives("bookshelf")[:2] == ["bookcase", "bookshelves"]
    assert asset_vocabulary.alternatives("rug")[0] == "carpet"
    assert "pillar" in asset_vocabulary.alternatives("column")


def test_a_qualifier_survives_the_swap():
    assert "round carpet" in asset_vocabulary.alternatives("round rug")


def test_unknown_words_have_no_alternatives_and_never_echo_the_term():
    assert asset_vocabulary.alternatives("zzqx") == []
    assert "rug" not in asset_vocabulary.alternatives("rug")


def test_alternatives_are_capped():
    assert len(asset_vocabulary.alternatives("chair stool")) <= asset_vocabulary.MAX_ALTERNATIVES


# --- notes ------------------------------------------------------------------


def test_notes_round_trip_and_an_empty_note_clears():
    saved = server.annotate_assets(
        [server.AssetNote(asset=SHELF, note="L-shaped corner unit", role="corner shelf")]
    )
    assert saved["saved"] == [SHELF]
    assert asset_notes.notes_for([SHELF, CARPET])[SHELF]["role"] == "corner shelf"
    assert asset_notes.indexed([CARPET, SHELF]) == {"1": "corner shelf: L-shaped corner unit"}

    listed = server.list_asset_notes(pack="abc123")
    assert [row["asset"] for row in listed["notes"]] == [SHELF]
    assert server.list_asset_notes(search="corner unit")["total"] == 1
    assert server.list_asset_notes(role="avoid")["total"] == 0

    cleared = server.annotate_assets([server.AssetNote(asset=SHELF, note="")])
    assert cleared["cleared"] == [SHELF]
    assert asset_notes.load() == {}


def test_notes_refuse_what_is_not_an_asset_path_or_too_long():
    with pytest.raises(ValidationError):
        server.annotate_assets([server.AssetNote(asset="bookcase_1a", note="x")])
    with pytest.raises(ValidationError):
        server.annotate_assets([server.AssetNote(asset=SHELF, note="x" * 501)])
    with pytest.raises(ValidationError):
        server.annotate_assets([])


def test_a_damaged_notes_file_reads_as_empty_and_bad_entries_are_dropped():
    asset_notes.path().write_text("{not json", encoding="utf-8")
    assert asset_notes.load() == {}
    asset_notes.path().write_text(
        json.dumps({"assets": {SHELF: {"note": "fine"}, CARPET: {"note": 3}, "x": "y"}}),
        encoding="utf-8",
    )
    assert list(asset_notes.load()) == [SHELF]


def test_a_rewrite_inside_one_timestamp_tick_is_still_read():
    """CI on Windows: two writes sharing an mtime served the first file's notes."""
    import os

    notes_file = asset_notes.path()
    notes_file.write_text(json.dumps({"assets": {}}), encoding="utf-8")
    assert asset_notes.load() == {}
    stamp = notes_file.stat().st_mtime_ns
    notes_file.write_text(json.dumps({"assets": {SHELF: {"note": "corner"}}}), encoding="utf-8")
    os.utime(notes_file, ns=(stamp, stamp))
    assert list(asset_notes.load()) == [SHELF]


# --- list_assets ------------------------------------------------------------


def _bridge(monkeypatch, answer):
    calls = []

    def request(command, **params):
        calls.append((command, params))
        return answer(command, params)

    monkeypatch.setattr(server.bridge, "request", request)
    return calls


def test_sizes_and_notes_ride_along_with_a_substring_listing(monkeypatch):
    server.annotate_assets([server.AssetNote(asset=CARPET_B, note="oval")])
    _bridge(
        monkeypatch,
        lambda command, params: {
            "assets": [CARPET, CARPET_B],
            "sizes": [[334, 340], [391, 476]],
            "colorable": [],
        },
    )
    result = server.list_assets("Objects", "carpet")
    assert result["sizes"] == [[334, 340], [391, 476]]
    assert result["notes"] == {"1": "oval"}
    assert "woxels" in result["sizes_are"]


def test_ranked_sizes_follow_the_ranked_order_not_the_bridges(monkeypatch):
    def answer(command, params):
        if "only" in params:
            # The bridge answers `only=` in category order.
            return {"assets": [CARPET, CARPET_B], "sizes": [[1, 1], [2, 2]], "colorable": []}
        return {"assets": [CARPET_B, CARPET], "matched": 2}

    _bridge(monkeypatch, answer)
    result = server.list_assets("Objects", "carpet 2a", match_mode="tokens")
    assert result["assets"] == [CARPET_B]
    assert result["sizes"] == [[2, 2]]


def test_an_older_bridge_without_sizes_lists_as_before(monkeypatch):
    _bridge(monkeypatch, lambda command, params: {"assets": [CARPET], "colorable": []})
    result = server.list_assets("Objects", "carpet")
    assert "sizes" not in result and "sizes_are" not in result


def test_a_blank_term_is_retried_under_another_name_and_says_so(monkeypatch):
    def answer(command, params):
        if params.get("search") == "carpet":
            return {"assets": [CARPET], "colorable": []}
        return {"assets": [], "colorable": []}

    calls = _bridge(monkeypatch, answer)
    result = server.list_assets("Objects", "rug")
    assert result["assets"] == [CARPET]
    assert result["matched_with"] == "carpet"
    assert "rug" in result["note"]
    assert [params["search"] for _, params in calls] == ["rug", "carpet"]


def test_a_term_that_matched_is_never_second_guessed(monkeypatch):
    calls = _bridge(monkeypatch, lambda command, params: {"assets": [CARPET], "colorable": []})
    result = server.list_assets("Objects", "rug")
    assert "matched_with" not in result
    assert len(calls) == 1


def test_multi_search_retries_only_its_blank_terms(monkeypatch):
    def answer(command, params):
        found = {"carpet": [CARPET], "bookcase": [SHELF]}.get(params.get("search"), [])
        return {"assets": found, "colorable": []}

    _bridge(monkeypatch, answer)
    result = server.list_assets("Objects", searches=["rug", "bookshelf", "zzqx"])
    assert result["results"]["rug"]["matched_with"] == "carpet"
    assert result["results"]["bookshelf"]["assets"] == [SHELF]
    assert result["results"]["zzqx"]["assets"] == []
    assert result["matched_with"] == {"rug": "carpet", "bookshelf": "bookcase"}
    assert "zzqx" in result["note"]


def test_pack_confines_the_listing_by_id_or_name(monkeypatch):
    def answer(command, params):
        if command == "list_asset_packs":
            return {"included_in_this_map": [{"id": "AbC123", "name": "CH - Dungeondraft"}]}
        return {"assets": [CARPET], "colorable": []}

    calls = _bridge(monkeypatch, answer)
    server.list_assets("Objects", "carpet", pack="ch - dungeondraft")
    assert calls[-1][1]["terms"] == ["packs/abc123/"]
    server.list_assets("Objects", "carpet", pack="AbC123", match_mode="tokens")
    candidate_terms = [params["terms"] for _, params in calls if "terms" in params]
    assert candidate_terms[-1] == ["carpet", "packs/abc123/"]


def test_an_unknown_pack_is_refused_with_the_choices(monkeypatch):
    _bridge(
        monkeypatch,
        lambda command, params: {"included_in_this_map": [{"id": "AbC123", "name": "Mine"}]},
    )
    with pytest.raises(ValidationError, match="AbC123"):
        server.list_assets("Objects", "carpet", pack="nope")


# --- preview caption --------------------------------------------------------


def test_the_preview_caption_names_each_cell_with_its_size_and_note():
    server.annotate_assets([server.AssetNote(asset=SHELF, note="corner unit", role="avoid")])
    caption = server._preview_caption(
        [CARPET, SHELF, CARPET_B],
        {
            "sizes": {
                CARPET: {"size": [334, 340], "opaque_rect": [0, 0, 334, 340]},
                SHELF: {"size": [300, 300], "opaque_rect": [10.0, 20.0, 280.0, 260.0]},
            },
            "missing": [CARPET_B],
        },
    )
    lines = caption.splitlines()
    assert lines[1] == f"1. {CARPET} — 334x340"
    assert lines[2] == f"2. {SHELF} — 300x300, drawn 280x260 at (10,20) — note: avoid: corner unit"
    assert lines[3] == f"3. {CARPET_B} — could not be loaded"
