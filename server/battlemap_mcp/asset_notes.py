"""What earlier sessions learned about individual assets, kept between sessions.

An asset's name does not say what it is. `bookcase_1a` in one painterly pack is
an L-shaped corner unit, a candelabra in another is drawn side-on and cannot
stand on a top-down table, and a cart called `cart_1a` is four tiles long. Each
of those cost a build a preview, a test placement or a rebuild to discover, and
the next session started knowing none of it.

Notes are short free text against an asset path, with an optional `role` saying
what the asset is FOR ("wall shelf", "corner shelf", "avoid"). They are written
by the assistant through `annotate_assets`, surfaced next to the asset wherever
`list_assets` or `preview_assets` return it, and browsed with
`list_asset_notes` before choosing a pack's assets.

They live in the integration's state folder as one JSON file, not in a map or a
pack: what a session learned about an asset is true of that asset everywhere.
The file is the user's data. Reads tolerate a missing or damaged file; writes
replace it atomically, so a crash mid-write leaves the previous notes intact.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .state_paths import state_dir

NOTES_FILE = "asset_notes.json"
FORMAT_VERSION = 1
MAX_NOTE_CHARS = 500
MAX_ROLE_CHARS = 40

# Keyed on the file's modification time AND size: two writes inside one
# timestamp tick (coarse on some Windows file systems) share an mtime, and
# keying on that alone served the first file's notes for the second.
_cache: tuple[tuple[int, int], dict[str, dict]] | None = None


def path() -> Path:
    return state_dir() / NOTES_FILE


def _clean(raw: Any) -> dict[str, dict]:
    """Keep only well-formed entries; a hand-edited file must not break listing."""
    assets = raw.get("assets") if isinstance(raw, dict) else None
    if not isinstance(assets, dict):
        return {}
    out: dict[str, dict] = {}
    for asset, entry in assets.items():
        if not isinstance(asset, str) or not isinstance(entry, dict):
            continue
        note = entry.get("note")
        if not isinstance(note, str) or not note.strip():
            continue
        out[asset] = {
            "note": note,
            "role": str(entry.get("role", "") or ""),
            "category": str(entry.get("category", "") or ""),
            "updated": str(entry.get("updated", "") or ""),
        }
    return out


def load() -> dict[str, dict]:
    """Every note by asset path, re-read when the file changes; {} if there is none."""
    global _cache
    try:
        stat = path().stat()
    except OSError:
        _cache = None
        return {}
    key = (stat.st_mtime_ns, stat.st_size)
    if _cache is not None and _cache[0] == key:
        return _cache[1]
    try:
        data = _clean(json.loads(path().read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        data = {}
    _cache = (key, data)
    return data


def _write(notes: dict[str, dict]) -> None:
    global _cache
    target = path()
    target.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(
        {"version": FORMAT_VERSION, "assets": dict(sorted(notes.items()))},
        indent=1,
        ensure_ascii=False,
    )
    handle, temporary = tempfile.mkstemp(prefix=".asset_notes-", dir=target.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(body + "\n")
        os.replace(temporary, target)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    _cache = None


def notes_for(assets: list[str]) -> dict[str, dict]:
    """The notes that exist for these paths, keyed by path."""
    known = load()
    return {asset: known[asset] for asset in assets if asset in known}


def indexed(assets: list[str]) -> dict[str, str]:
    """Notes for a listing as {index: "role: note"}, the way `colorable` uses indices."""
    known = load()
    out: dict[str, str] = {}
    for index, asset in enumerate(assets):
        entry = known.get(asset)
        if entry is not None:
            out[str(index)] = (
                f"{entry['role']}: {entry['note']}" if entry["role"] else entry["note"]
            )
    return out


def apply(changes: list[dict]) -> dict[str, list[str]]:
    """Set or clear several notes in one write. An empty note clears that asset's.

    Each change carries `asset`, `note` and optionally `role` and `category`,
    already validated by the caller.
    """
    notes = dict(load())
    today = datetime.now(UTC).date().isoformat()
    saved: list[str] = []
    cleared: list[str] = []
    for change in changes:
        asset = change["asset"]
        note = change["note"].strip()
        if not note:
            if notes.pop(asset, None) is not None:
                cleared.append(asset)
            continue
        notes[asset] = {
            "note": note,
            "role": change.get("role", "").strip(),
            "category": change.get("category", "").strip(),
            "updated": today,
        }
        saved.append(asset)
    if saved or cleared:
        _write(notes)
    return {"saved": saved, "cleared": cleared}


def search(query: str = "", pack: str = "", role: str = "") -> list[dict]:
    """Notes whose path, note or role contain every query word, newest first."""
    words = [word for word in query.lower().split() if word]
    pack_marker = f"/packs/{pack.lower()}/" if pack else ""
    out = []
    for asset, entry in load().items():
        haystack = f"{asset} {entry['note']} {entry['role']}".lower()
        if pack_marker and pack_marker not in asset.lower():
            continue
        if role and role.lower() not in entry["role"].lower():
            continue
        if any(word not in haystack for word in words):
            continue
        out.append({"asset": asset, **entry})
    out.sort(key=lambda row: (row["updated"], row["asset"]), reverse=True)
    return out
