"""Access and mutate deeply nested dicts using dot-notation paths."""

from __future__ import annotations

import re
from typing import Any

__all__ = ["get", "set", "delete", "has", "flatten", "unflatten"]

_MISSING = object()

_INDEX_RE = re.compile(r"^([^\[]+)\[(\d+|\*)\]$")


def _parse_path(path: str) -> list[str | int]:
    """Parse a dot-notation path into a list of keys and indices.

    Supports dot notation (``a.b.c``), integer indices (``a[0].b``),
    and wildcard indices (``a[*].b``).
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
    """
    parts = _parse_path(path)
    current: Any = data
    for part in parts[:-1]:
        if isinstance(part, int):
            try:
                current = current[part]
            except (IndexError, TypeError) as exc:
                raise KeyError(part) from exc
        elif part == "*":
            raise ValueError("Wildcard '*' is not supported in set()")
        else:
            if part not in current or not isinstance(current.get(part), dict):
                current[part] = {}
            current = current[part]

    last = parts[-1]
    if isinstance(last, int):
        try:
            current[last] = value
        except (IndexError, TypeError) as exc:
            raise KeyError(last) from exc
    elif last == "*":
        raise ValueError("Wildcard '*' is not supported in set()")
    else:
        current[last] = value


def delete(data: dict[str, Any], path: str) -> None:
    """Delete the key at *path*.

    Raises :class:`KeyError` if the path does not exist.
    """
    parts = _parse_path(path)
    current: Any = data
    for part in parts[:-1]:
        if isinstance(part, int):
            try:
                current = current[part]
            except (IndexError, TypeError) as exc:
                raise KeyError(part) from exc
        elif part == "*":
            raise ValueError("Wildcard '*' is not supported in delete()")
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
    elif last == "*":
        raise ValueError("Wildcard '*' is not supported in delete()")
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
