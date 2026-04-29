# Changelog

## 0.3.0 (2026-04-29)

- Add `paths()` — lazy iterator over every leaf path (companion to `flatten()`)
- Fix `set()` clobbering existing lists when traversing through them via dot path (e.g. `set(data, "users[0].name", x)` previously overwrote `users` with `{}`)
- Replace import-only stub with real test suite covering get/set/has/delete/pop/merge/search/flatten/unflatten/paths and the regression
- Clean up malformed CHANGELOG history (collapsed `0.2.1` and `0.2.2` entries split out)

## 0.2.3 (2026-03-31)

- Standardize README to 3-badge format with emoji Support section
- Update CI checkout action to v5 for Node.js 24 compatibility
- Add GitHub issue templates, dependabot config, and PR template

## 0.2.2

- Trim keywords to match pyproject template guide

## 0.2.1

- Add pytest and mypy tool configuration to pyproject.toml

## 0.2.0 (2026-03-16)

- Support wildcards in `set()` and `delete()` (e.g., `set(data, "users[*].active", True)`)
- Add negative indexing (e.g., `get(data, "users[-1].name")`)
- Add `pop()` — remove and return value at path
- Add `merge()` — deep-merge a dict into a nested path
- Add `search()` — find all paths matching a predicate

## 0.1.5

- Add basic import test

## 0.1.4

- Add Development section to README

## 0.1.1

- Re-release for PyPI publishing

## 0.1.0 (2026-03-15)

- Initial release
- `get()` — retrieve values at dot-notation paths with optional default
- `set()` — set values, creating intermediate dicts automatically
- `delete()` — remove keys at dot-notation paths
- `has()` — check if a path exists
- `flatten()` — flatten nested dicts into single-level dicts
- `unflatten()` — restore flattened dicts to nested structure
- Array index support: `users[0].name`
- Wildcard support: `users[*].email`
