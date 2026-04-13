# Code Conventions

These are the coding conventions for this project. Follow them closely — they are
intentional and reflect the project's values.

## Philosophy

- **Low cognitive load.** Code reads top-to-bottom without jumping around.
- **Pure by default.** Push I/O to the boundary. Models and helpers are pure functions.
  Defaults and configuration values (API keys, base URLs, feature flags) belong in the
  CLI layer — not in library modules. Library functions accept these as parameters; the
  CLI decides the values.
- **No over-engineering.** Don't build abstractions until you have two concrete uses.
- **Defer what you don't need.** If a feature isn't needed yet, don't add it.

## Code Style

### No underscore prefixes

Don't use `_` to signal "private." In Python everything is accessible regardless, so
the prefix is noise that conveys nothing the code structure doesn't already show. A
function only called by one other function in the same module is obviously a helper —
you can see that from usage. If it's in the module, it's part of the module.

The real "private" boundary is what you choose to test, not a naming convention. Test
through the public-facing functions; helpers get coverage indirectly. If you refactor
a helper away, no tests break.

### Functions over methods

If it doesn't need `self`, it's a standalone function, not a method. Compose small
functions rather than building class hierarchies.

```python
# Yes
def columns(cursor):
    return [desc[0] for desc in cursor.description]

def row(cols, values):
    return dict(zip(cols, values))

# No
class SomeStore:
    def _get_columns(self, cursor): ...
    def _row_to_dict(self, cols, values): ...
```

### Default arguments for configurability

Never reference module-level constants directly inside function bodies. Instead, pass
them as default arguments. This makes functions testable and reusable without adding
configuration infrastructure. For classes, use class attributes instead of reaching for
the global.

```python
# Yes — constant flows through the signature
def find_config_dir(start=None, dirname=CONFIG_DIR) -> Path: ...

# Yes — class owns its configuration
class SomeId(str):
    prefix = ID_PREFIX
    def __new__(cls, value="", **kwargs):
        if not value.startswith(cls.prefix): ...

# No — function reaches for the global directly
def find_config_dir(start=None) -> Path:
    candidate = current / CONFIG_DIR  # hidden dependency
```

### `**kwargs` over dict for named fields

When a function accepts a set of named fields, use `**kwargs` instead of a dict parameter.
It reads better at the call site and lets the interpreter catch typos.

```python
# Yes
def update(self, item_id, **fields) -> int: ...
store.update(item_id, title="New title", status="closed")

# No
def update(self, item_id, fields: dict) -> int: ...
store.update(item_id, {"title": "New title", "status": "closed"})
```

### Constants for magic values

```python
ID_BYTES = 4
```

### Let Pydantic handle coercion

Don't manually convert what Pydantic validates and coerces automatically. For example,
Pydantic coerces ISO strings to datetime — don't call `fromisoformat()` yourself.

### Import organization

Use section comments and `force-sort-within-sections`:

```python
# Python imports
import json
import sqlite3

# Pip imports
import typer

# Internal imports
from mypackage.models import MyModel
```

### Type annotations

Annotate return types. Don't annotate parameters when the default value tells the story.

## Dependency Injection

### Inject, don't construct

Classes take their dependencies as arguments, not paths or config. Factory classmethods
handle construction. This enables testing with in-memory or fake backends.

```python
# Production
store = MyStore.from_path("data.db")

# Testing
store = MyStore(sqlite3.connect(":memory:"))
```

### Context manager protocol

Resource-holding classes implement `__enter__`/`__exit__` to avoid explicit `close()`.

```python
with MyStore.from_path("data.db") as store:
    store.create(item)
```

### Model stays pure, display lives in CLI

Don't add `__str__` or `__format__` to models for display purposes. Display formatting
is a CLI concern — use standalone functions like `format_item()`.

## CLI

### argparse (not Typer)

This project uses **argparse** — not Typer or Click. The Jira field schema is dynamic
(varies per instance), and the core commands use `--set key=value` / `--json '{...}'`
for field input. Decorator-based frameworks fight this; argparse gives full runtime
control with no dependencies.

### `parse` / `cli` split

Separate parsing from execution for testability:

```python
def parse(argv=None) -> argparse.Namespace:
    """Pure parsing. Returns a Namespace. No I/O."""
    ...

def cli(argv=None):
    """Entry point. Parses, dispatches, handles I/O."""
    args = parse(argv)
    ...
```

Test `parse()` directly — no `CliRunner` needed:

```python
def test_issue_get_parses_key():
    args = parse(["issue", "get", "DEV-123"])
    assert args.command == "issue"
    assert args.subcommand == "get"
    assert args.key == "DEV-123"
```
