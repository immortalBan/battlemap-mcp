"""Named groups of placed elements, so a zone can be reworked as one thing.

Reworking "the south reading tables" meant reverse-engineering their ids from
the order of a JSON file; the name the build had in mind was nowhere. Placement
tools take `group`, and delete_elements, move_elements, fit_elements and
list_groups take it back.

Groups live in this companion process, for the session: they are a working
aid, not map data. Element ids are Dungeondraft's own node ids, stable while
the map is open; a group is not saved into the map and does not survive a
restart of the companion. Members deleted through this companion leave their
groups; one removed some other way is dropped when the group is next resolved.
"""

from __future__ import annotations

import re

_NAME = re.compile(r"[\w][\w ./:-]{0,59}\Z")
_groups: dict[str, list[int]] = {}


def check_name(name: str) -> str:
    """The group name as given, or ValueError naming what is allowed."""
    cleaned = name.strip()
    if not _NAME.match(cleaned):
        raise ValueError(
            f"group {name!r} is not a usable name: 1-60 letters, digits, spaces, "
            "'_', '-', '.', '/' or ':', starting with a letter or digit"
        )
    return cleaned


def add(name: str, ids: list[int]) -> None:
    """Add ids to a group, creating it; an id already in it is not repeated."""
    members = _groups.setdefault(check_name(name), [])
    for ident in ids:
        if ident not in members:
            members.append(int(ident))


def members(name: str) -> list[int]:
    """The group's ids in the order they joined; KeyError if there is no such group."""
    cleaned = name.strip()
    if cleaned not in _groups:
        raise KeyError(cleaned)
    return list(_groups[cleaned])


def keep(name: str, alive: set[int]) -> list[int]:
    """Drop members that no longer exist, and return the rest."""
    cleaned = name.strip()
    _groups[cleaned] = [ident for ident in _groups.get(cleaned, []) if ident in alive]
    return list(_groups[cleaned])


def forget(ids: list[int]) -> None:
    """Remove deleted ids from every group; a group left empty disappears."""
    gone = {int(ident) for ident in ids}
    for name in list(_groups):
        _groups[name] = [ident for ident in _groups[name] if ident not in gone]
        if not _groups[name]:
            del _groups[name]


def all_groups() -> dict[str, list[int]]:
    return {name: list(ids) for name, ids in sorted(_groups.items())}


def clear() -> None:
    _groups.clear()
