# Changelog

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
