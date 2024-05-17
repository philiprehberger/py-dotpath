# philiprehberger-dotpath

[![Tests](https://github.com/philiprehberger/py-dotpath/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-dotpath/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-dotpath.svg)](https://pypi.org/project/philiprehberger-dotpath/)
[![License](https://img.shields.io/github/license/philiprehberger/py-dotpath)](LICENSE)
[![Sponsor](https://img.shields.io/badge/sponsor-GitHub%20Sponsors-ec6cb9)](https://github.com/sponsors/philiprehberger)

Access and mutate deeply nested dicts using dot-notation paths.

## Installation

```bash
pip install philiprehberger-dotpath
```

## Usage

```python
from philiprehberger_dotpath import get, set, has, delete, flatten, unflatten, pop, merge, search

data = {"users": [{"name": "Alice", "email": "alice@example.com"}]}

# Get a value
get(data, "users[0].name")        # "Alice"

# Get with default
get(data, "users[0].phone", default=None)  # None

# Set a value (creates intermediate dicts)
set(data, "users[0].address.city", "Berlin")

# Check existence
has(data, "users[0].address.city")  # True

# Delete a key
delete(data, "users[0].address.city")
```

### Wildcards

```python
data = {"users": [{"email": "a@b.com"}, {"email": "c@d.com"}]}

get(data, "users[*].email")  # ["a@b.com", "c@d.com"]

# Set a field on all items
set(data, "users[*].active", True)
# data["users"] == [{"email": "a@b.com", "active": True}, {"email": "c@d.com", "active": True}]

# Delete a field from all items
delete(data, "users[*].active")
```

### Negative Indexing

```python
data = {"items": [{"name": "a"}, {"name": "b"}, {"name": "c"}]}

get(data, "items[-1].name")      # "c"
set(data, "items[-2].name", "B") # updates second-to-last
```

### Pop

```python
data = {"a": {"b": 1, "c": 2}}

pop(data, "a.b")               # 1  (key removed)
pop(data, "a.missing", default=0)  # 0  (no error)
```

### Merge

```python
data = {"config": {"db": {"host": "localhost", "port": 3306}}}

merge(data, "config.db", {"port": 5432, "name": "mydb"})
# data["config"]["db"] == {"host": "localhost", "port": 5432, "name": "mydb"}
```

### Search

```python
data = {"a": 1, "b": {"c": 2, "d": [10, 20]}}

search(data, lambda v: isinstance(v, int) and v > 5)
# ["b.d[0]", "b.d[1]"]
```

### Flatten and Unflatten

```python
nested = {"a": {"b": {"c": 1}}, "d": [10, 20]}

flatten(nested)
# {"a.b.c": 1, "d[0]": 10, "d[1]": 20}

unflatten({"a.b.c": 1, "d[0]": 10, "d[1]": 20})
# {"a": {"b": {"c": 1}}, "d": [10, 20]}
```

## API

| Function | Description |
|----------|-------------|
| `get(data, path, *, default=_MISSING)` | Get value at dot path; raises `KeyError` if missing and no default |
| `set(data, path, value)` | Set value at dot path, creating intermediate dicts; supports wildcards |
| `delete(data, path)` | Delete the key at dot path; supports wildcards |
| `has(data, path) -> bool` | Check whether a path exists |
| `pop(data, path, *, default=_MISSING)` | Remove and return value at path; like `dict.pop()` |
| `merge(data, path, value)` | Deep-merge a dict into the dict at path |
| `search(data, predicate) -> list[str]` | Find all dot-paths where `predicate(value)` is `True` |
| `flatten(data, *, separator=".") -> dict` | Flatten nested dict to single level |
| `unflatten(data, *, separator=".") -> dict` | Restore flattened dict to nested structure |


## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## License

MIT
