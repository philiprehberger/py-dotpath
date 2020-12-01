# philiprehberger-dotpath

[![Tests](https://github.com/philiprehberger/py-dotpath/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-dotpath/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-dotpath.svg)](https://pypi.org/project/philiprehberger-dotpath/)
[![License](https://img.shields.io/github/license/philiprehberger/py-dotpath)](LICENSE)

Access and mutate deeply nested dicts using dot-notation paths.

## Install

```bash
pip install philiprehberger-dotpath
```

## Usage

```python
from philiprehberger_dotpath import get, set, has, delete, flatten, unflatten

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
| `set(data, path, value)` | Set value at dot path, creating intermediate dicts |
| `delete(data, path)` | Delete the key at dot path |
| `has(data, path) -> bool` | Check whether a path exists |
| `flatten(data, *, separator=".") -> dict` | Flatten nested dict to single level |
| `unflatten(data, *, separator=".") -> dict` | Restore flattened dict to nested structure |


## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## License

MIT
