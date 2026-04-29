"""Tests for philiprehberger_dotpath."""

from __future__ import annotations

import pytest

from philiprehberger_dotpath import (
    delete,
    flatten,
    get,
    has,
    merge,
    paths,
    pop,
    search,
    set,
    unflatten,
)


class TestGet:
    def test_simple_path(self) -> None:
        assert get({"a": 1}, "a") == 1

    def test_nested_path(self) -> None:
        assert get({"a": {"b": {"c": 5}}}, "a.b.c") == 5

    def test_with_index(self) -> None:
        data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        assert get(data, "users[0].name") == "Alice"

    def test_negative_index(self) -> None:
        data = {"items": ["a", "b", "c"]}
        assert get(data, "items[-1]") == "c"

    def test_missing_returns_default(self) -> None:
        assert get({}, "missing", default=None) is None
        assert get({}, "missing", default=42) == 42

    def test_missing_raises_without_default(self) -> None:
        with pytest.raises(KeyError):
            get({}, "missing")

    def test_wildcard_collects(self) -> None:
        data = {"users": [{"name": "A"}, {"name": "B"}]}
        assert get(data, "users[*].name") == ["A", "B"]


class TestSet:
    def test_creates_nested_dicts(self) -> None:
        data: dict = {}
        set(data, "a.b.c", 1)
        assert data == {"a": {"b": {"c": 1}}}

    def test_overwrites_existing_value(self) -> None:
        data = {"a": 1}
        set(data, "a", 2)
        assert data["a"] == 2

    def test_set_with_index(self) -> None:
        data: dict = {"users": [{"name": "Old"}]}
        set(data, "users[0].name", "Alice")
        assert data["users"][0]["name"] == "Alice"

    def test_set_wildcard(self) -> None:
        data = {"users": [{"name": "A"}, {"name": "B"}]}
        set(data, "users[*].active", True)
        assert all(u["active"] for u in data["users"])


class TestHasAndDelete:
    def test_has_true(self) -> None:
        assert has({"a": {"b": 1}}, "a.b")

    def test_has_false(self) -> None:
        assert not has({"a": {"b": 1}}, "a.c")

    def test_delete(self) -> None:
        data = {"a": {"b": 1, "c": 2}}
        delete(data, "a.b")
        assert "b" not in data["a"]
        assert "c" in data["a"]

    def test_delete_wildcard_field(self) -> None:
        data = {"users": [{"name": "A", "x": 1}, {"name": "B", "x": 2}]}
        delete(data, "users[*].x")
        assert all("x" not in u for u in data["users"])


class TestPop:
    def test_pop_returns_and_removes(self) -> None:
        data = {"a": {"b": 5}}
        value = pop(data, "a.b")
        assert value == 5
        assert "b" not in data["a"]

    def test_pop_default(self) -> None:
        assert pop({}, "missing", default="x") == "x"


class TestMerge:
    def test_merge_into_nested_path(self) -> None:
        data = {"config": {"db": {"host": "localhost"}}}
        merge(data, "config.db", {"port": 5432, "name": "mydb"})
        assert data["config"]["db"] == {"host": "localhost", "port": 5432, "name": "mydb"}


class TestSearch:
    def test_search_returns_matching_paths(self) -> None:
        data = {"a": {"b": 1, "c": 2}, "d": [10, 20]}
        results = search(data, lambda v: isinstance(v, int) and v >= 10)
        assert "d[0]" in results
        assert "d[1]" in results


class TestFlattenUnflatten:
    def test_flatten_round_trip(self) -> None:
        nested = {"a": {"b": {"c": 1}}, "d": [10, 20]}
        flat = flatten(nested)
        assert flat == {"a.b.c": 1, "d[0]": 10, "d[1]": 20}
        assert unflatten(flat) == nested


class TestPaths:
    def test_lists_leaf_paths(self) -> None:
        data = {"a": {"b": 1}, "c": 2}
        assert sorted(paths(data)) == ["a.b", "c"]

    def test_lists_indexed_paths(self) -> None:
        data = {"items": [10, 20]}
        assert sorted(paths(data)) == ["items[0]", "items[1]"]

    def test_is_iterator(self) -> None:
        gen = paths({"a": 1})
        assert iter(gen) is gen
        assert list(gen) == ["a"]

    def test_empty_dict_yields_nothing(self) -> None:
        assert list(paths({})) == []

    def test_custom_separator(self) -> None:
        data = {"a": {"b": 1}}
        assert list(paths(data, separator="/")) == ["a/b"]

    def test_matches_flatten_keys(self) -> None:
        data = {"a": {"b": [1, 2]}, "c": 3}
        assert sorted(paths(data)) == sorted(flatten(data).keys())
