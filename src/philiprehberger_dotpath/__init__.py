"""Access and mutate deeply nested dicts using dot-notation paths."""

from __future__ import annotations

import re
from typing import Any, Callable, Iterator

__all__ = [
    "get",
    "set",
    "delete",
    "has",
    "flatten",
    "unflatten",
    "pop",
    "merge",
    "paths",
    "search",
]

_MISSING = object()

_INDEX_RE = re.compile(r"^([^\[]+)\[(-?\d+|\*)\]$")


def _parse_path(path: str) -> list[str | int]:
    """Parse a dot-notation path into a list of keys and indices.

    Supports dot notation (``a.b.c``), integer indices (``a[0].b``),
    negative indices (``a[-1].b``), and wildcard indices (``a[*].b``).
    """
    parts: list[str | int] = []
    for segment in path.split("."):
        m = _INDEX_RE.match(segment)
        if m:
            parts.append(m.group(1))
            idx = m.group(2)
            parts.append("*" if idx == "*" else int(idx))
        else:
            parts.append(segment)
    return parts


def _resolve(data: Any, parts: list[str | int], *, collect: bool = False) -> Any:
    """Walk *data* along *parts*, returning the value at the end.

    When *collect* is ``True`` and a wildcard ``*`` index is
    encountered, all matching elements are gathered into a list.
    """
    current: Any = data
    for i, part in enumerate(parts):
        if part == "*":
            if not isinstance(current, list):
                raise KeyError(f"Wildcard on non-list value")
            remaining = parts[i + 1 :]
            if remaining:
                return [_resolve(item, remaining, collect=True) for item in current]
            return list(current)
        if isinstance(part, int):
            try:
                current = current[part]
            except (IndexError, TypeError) as exc:
                raise KeyError(part) from exc
        else:
            if not isinstance(current, dict):
                raise KeyError(part)
            if part not in current:
                raise KeyError(part)
            current = current[part]
    return current


def _walk_wildcard_set(
    data: Any,
    parts: list[str | int],
    idx: int,
    value: Any,
) -> None:
    """Recursively walk to wildcards in *parts* and set *value* on each match."""
    current: Any = data
    for i in range(idx, len(parts) - 1):
        part = parts[i]
        if part == "*":
            if not isinstance(current, list):
                raise KeyError("Wildcard on non-list value")
            for item in current:
                _walk_wildcard_set(item, parts, i + 1, value)
            return
        if isinstance(part, int):
            try:
                current = current[part]
            except (IndexError, TypeError) as exc:
                raise KeyError(part) from exc
        else:
            if isinstance(current, dict):
                if part not in current:
                    current[part] = {}
                current = current[part]
            else:
                raise KeyError(part)

    last = parts[-1]
    if last == "*":
        if not isinstance(current, list):
            raise KeyError("Wildcard on non-list value")
        for j in range(len(current)):
            current[j] = value
    elif isinstance(last, int):
        try:
            current[last] = value
        except (IndexError, TypeError) as exc:
            raise KeyError(last) from exc
    else:
        if isinstance(current, dict):
            current[last] = value
        elif isinstance(current, list):
            for item in current:
                if isinstance(item, dict):
                    item[last] = value
        else:
            raise KeyError(last)


def _walk_wildcard_delete(
    data: Any,
    parts: list[str | int],
    idx: int,
) -> None:
    """Recursively walk to wildcards in *parts* and delete the final key."""
    current: Any = data
    for i in range(idx, len(parts) - 1):
        part = parts[i]
        if part == "*":
            if not isinstance(current, list):
                raise KeyError("Wildcard on non-list value")
            for item in current:
                _walk_wildcard_delete(item, parts, i + 1)
            return
        if isinstance(part, int):
            try:
                current = current[part]
            except (IndexError, TypeError) as exc:
                raise KeyError(part) from exc
        else:
            if not isinstance(current, dict) or part not in current:
                raise KeyError(part)
            current = current[part]

    last = parts[-1]
    if last == "*":
        if not isinstance(current, list):
            raise KeyError("Wildcard on non-list value")
        current.clear()
    elif isinstance(last, int):
        try:
            del current[last]
        except (IndexError, TypeError) as exc:
            raise KeyError(last) from exc
    else:
        if not isinstance(current, dict) or last not in current:
            raise KeyError(last)
        del current[last]


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> None:
    """Recursively merge *source* into *target*."""
    for key, val in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(val, dict):
            _deep_merge(target[key], val)
        else:
            target[key] = val


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def get(data: dict[str, Any], path: str, *, default: Any = _MISSING) -> Any:
    """Return the value at *path* inside *data*.

    Parameters
    ----------
    data:
        The nested dictionary to query.
    path:
        Dot-notation path, e.g. ``"users[0].name"`` or ``"users[*].email"``.
        Negative indices are supported, e.g. ``"users[-1].name"``.
    default:
        Value to return when the path does not exist.  If omitted a
        :class:`KeyError` is raised for missing paths.
    """
    parts = _parse_path(path)
    try:
        return _resolve(data, parts, collect=True)
    except KeyError:
        if default is _MISSING:
            raise
        return default


def set(data: dict[str, Any], path: str, value: Any) -> None:
    """Set the *value* at *path*, creating intermediate dicts as needed.

    Integer indices are supported for existing lists, but new lists are
    **not** auto-created — intermediate containers are always dicts.

    Wildcards are supported: ``set(data, "users[*].active", True)``
    sets the field on every item in the list.
    """
    parts = _parse_path(path)
    if "*" in parts:
        _walk_wildcard_set(data, parts, 0, value)
        return

    current: Any = data
    for part in parts[:-1]:
        if isinstance(part, int):
            try:
                current = current[part]
            except (IndexError, TypeError) as exc:
                raise KeyError(part) from exc
        else:
            existing = current.get(part) if isinstance(current, dict) else None
            if part not in current or not isinstance(existing, (dict, list)):
                current[part] = {}
            current = current[part]

    last = parts[-1]
    if isinstance(last, int):
        try:
            current[last] = value
        except (IndexError, TypeError) as exc:
            raise KeyError(last) from exc
    else:
        current[last] = value


def delete(data: dict[str, Any], path: str) -> None:
    """Delete the key at *path*.

    Raises :class:`KeyError` if the path does not exist.

    Wildcards are supported: ``delete(data, "users[*].temp")``
    deletes the field from every item in the list.
    """
    parts = _parse_path(path)
    if "*" in parts:
        _walk_wildcard_delete(data, parts, 0)
        return

    current: Any = data
    for part in parts[:-1]:
        if isinstance(part, int):
            try:
                current = current[part]
            except (IndexError, TypeError) as exc:
                raise KeyError(part) from exc
        else:
            if not isinstance(current, dict) or part not in current:
                raise KeyError(part)
            current = current[part]

    last = parts[-1]
    if isinstance(last, int):
        try:
            del current[last]
        except (IndexError, TypeError) as exc:
            raise KeyError(last) from exc
    else:
        if not isinstance(current, dict) or last not in current:
            raise KeyError(last)
        del current[last]


def has(data: dict[str, Any], path: str) -> bool:
    """Return ``True`` if *path* exists in *data*."""
    parts = _parse_path(path)
    try:
        _resolve(data, parts, collect=False)
        return True
    except KeyError:
        return False


def pop(data: dict[str, Any], path: str, *, default: Any = _MISSING) -> Any:
    """Remove and return the value at *path*.  Like :meth:`dict.pop`.

    Parameters
    ----------
    data:
        The nested dictionary to mutate.
    path:
        Dot-notation path to the value to remove.
    default:
        If provided and *path* does not exist, return *default* instead
        of raising :class:`KeyError`.
    """
    parts = _parse_path(path)
    current: Any = data
    try:
        for part in parts[:-1]:
            if isinstance(part, int):
                try:
                    current = current[part]
                except (IndexError, TypeError) as exc:
                    raise KeyError(part) from exc
            elif part == "*":
                raise KeyError("Wildcard '*' is not supported in pop()")
            else:
                if not isinstance(current, dict) or part not in current:
                    raise KeyError(part)
                current = current[part]

        last = parts[-1]
        if isinstance(last, int):
            try:
                value = current[last]
                del current[last]
                return value
            except (IndexError, TypeError) as exc:
                raise KeyError(last) from exc
        elif last == "*":
            raise KeyError("Wildcard '*' is not supported in pop()")
        else:
            if not isinstance(current, dict) or last not in current:
                raise KeyError(last)
            return current.pop(last)
    except KeyError:
        if default is _MISSING:
            raise
        return default


def merge(data: dict[str, Any], path: str, value: dict[str, Any]) -> None:
    """Deep-merge *value* into the dict at *path*.

    If *path* does not exist yet, it is created and set to *value*.
    If the existing value at *path* is a dict, *value* is recursively
    merged into it.
    """
    parts = _parse_path(path)
    try:
        existing = _resolve(data, parts, collect=False)
    except KeyError:
        existing = None

    if isinstance(existing, dict):
        _deep_merge(existing, value)
    else:
        set(data, path, value)


def search(data: dict[str, Any], predicate: Callable[[Any], bool]) -> list[str]:
    """Find all dot-paths where ``predicate(value)`` is ``True``.

    Recursively walks *data* (including nested dicts and lists) and
    returns a list of dot-notation path strings for every leaf or
    sub-tree where the predicate matches.

    >>> search({"a": 1, "b": {"c": 2}}, lambda v: isinstance(v, int) and v > 1)
    ['b.c']
    """
    results: list[str] = []

    def _walk(obj: Any, prefix: str) -> None:
        if isinstance(obj, dict):
            for key, val in obj.items():
                new_key = f"{prefix}.{key}" if prefix else key
                if predicate(val):
                    results.append(new_key)
                _walk(val, new_key)
        elif isinstance(obj, list):
            for i, val in enumerate(obj):
                new_key = f"{prefix}[{i}]"
                if predicate(val):
                    results.append(new_key)
                _walk(val, new_key)

    _walk(data, "")
    return results


def paths(data: dict[str, Any], *, separator: str = ".") -> Iterator[str]:
    """Yield every leaf path in *data* in dot/bracket notation.

    Companion to :func:`flatten` — paths are produced lazily so callers can
    iterate without materialising the full flattened dict.

    >>> list(paths({"a": {"b": 1}, "c": [10, 20]}))
    ['a.b', 'c[0]', 'c[1]']
    """

    def _walk(obj: Any, prefix: str) -> Iterator[str]:
        if isinstance(obj, dict):
            for key, val in obj.items():
                new_key = f"{prefix}{separator}{key}" if prefix else key
                yield from _walk(val, new_key)
        elif isinstance(obj, list):
            for i, val in enumerate(obj):
                yield from _walk(val, f"{prefix}[{i}]")
        else:
            yield prefix

    yield from _walk(data, "")


def flatten(data: dict[str, Any], *, separator: str = ".") -> dict[str, Any]:
    """Flatten a nested dict into a single-level dict.

    Keys are joined with *separator*.  List indices are represented
    with bracket notation (e.g. ``users[0].name``).

    >>> flatten({"a": {"b": 1}})
    {'a.b': 1}
    """
    result: dict[str, Any] = {}

    def _walk(obj: Any, prefix: str) -> None:
        if isinstance(obj, dict):
            for key, val in obj.items():
                new_key = f"{prefix}{separator}{key}" if prefix else key
                _walk(val, new_key)
        elif isinstance(obj, list):
            for i, val in enumerate(obj):
                new_key = f"{prefix}[{i}]"
                _walk(val, new_key)
        else:
            result[prefix] = obj

    _walk(data, "")
    return result


def unflatten(data: dict[str, Any], *, separator: str = ".") -> dict[str, Any]:
    """Unflatten a single-level dict into a nested dict.

    The inverse of :func:`flatten`.

    >>> unflatten({"a.b": 1})
    {'a': {'b': 1}}
    """
    result: dict[str, Any] = {}

    _bracket_re = re.compile(r"\[(\d+)\]")

    for compound_key, value in data.items():
        # Split on separator, then further split bracket indices
        raw_parts = compound_key.split(separator)
        parts: list[str | int] = []
        for raw in raw_parts:
            # Handle keys like "users[0]"
            segments = _bracket_re.split(raw)
            for j, seg in enumerate(segments):
                if not seg:
                    continue
                if j % 2 == 1:
                    parts.append(int(seg))
                else:
                    parts.append(seg)

        current: Any = result
        for i, part in enumerate(parts[:-1]):
            next_part = parts[i + 1]
            if isinstance(part, int):
                while len(current) <= part:
                    current.append({} if not isinstance(next_part, int) else [])
                current = current[part]
            else:
                if part not in current:
                    current[part] = [] if isinstance(next_part, int) else {}
                current = current[part]

        last = parts[-1]
        if isinstance(last, int):
            while len(current) <= last:
                current.append(None)
            current[last] = value
        else:
            current[last] = value

    return result
