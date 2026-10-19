"""The session registry behind `group`."""

from __future__ import annotations

import pytest

from battlemap_mcp import groups


def test_ids_join_once_in_order_and_survive_lookup():
    groups.add("hall", [3, 1, 3])
    groups.add("hall", [2])
    assert groups.members("hall") == [3, 1, 2]


def test_keep_and_forget_drop_what_no_longer_exists():
    groups.add("a", [1, 2, 3])
    groups.add("b", [3])
    assert groups.keep("a", {1, 3}) == [1, 3]
    groups.forget([3])
    assert groups.all_groups() == {"a": [1]}


@pytest.mark.parametrize("name", ["", "   ", "x" * 61, "bad|pipe", "-leading"])
def test_unusable_names_are_refused(name):
    with pytest.raises(ValueError):
        groups.check_name(name)


def test_an_unknown_group_raises_key_error():
    with pytest.raises(KeyError):
        groups.members("nope")
