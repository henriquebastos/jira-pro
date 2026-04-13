# Testing Conventions

## No mocks (when possible)

Prefer real backends (e.g. SQLite `:memory:`) over mocks. Test real behavior, not mock
wiring. Use mocks only for external services or I/O boundaries that can't be faked cheaply.

## Use `responses` for HTTP testing

This project uses the `responses` library to mock HTTP calls at the transport level,
the same pattern as requests-pro. Don't mock session classes or build fake adapters —
mock the HTTP endpoints directly:

```python
def test_renew_returns_tokens(self, tmp_path, responses):
    responses.add("POST", JiraAuth.TOKEN_URL, json={"access_token": "new", "expires_in": 3600})
    auth = make_auth(tmp_path, refresh_token="old")
    access_token, expires_in = auth.renew()
    assert access_token == "new"
```

The shared `responses` fixture lives in `tests/conftest.py`:

```python
@pytest.fixture()
def responses():
    with responses_lib.RequestsMock(assert_all_requests_are_fired=False) as mock:
        yield mock
```

## Check upstream test patterns

When using a private or less-known dependency, read its test suite before writing your
own tests. Clone the repo if needed. Match the upstream's testing patterns — they know
their library best.

## Assert against the model, not individual fields

Leverage Pydantic equality to compare whole objects. Don't decompose into field-by-field
checks when a single comparison says it all.

```python
# Yes — one assertion, full structural check
assert store.get(item.id) == item
assert store.list() == [i1, i2]

# No — decomposing what equality already covers
result = store.get(item.id)
assert result.id == item.id
assert result.title == "Fix auth"
```

For model defaults, use `model_dump()` against an expected dict with fixed `id` and
`created_at` to pin dynamic fields.

```python
def test_defaults(self):
    item = MyModel(id="item-00000000", title="Fix auth", created_at=FIXED_TIME)
    assert item.model_dump() == {
        "id": "item-00000000",
        "title": "Fix auth",
        "type": "task",
        ...
    }
```

## Module-level fixtures for shared infrastructure

Extract common fixtures (like `store`) to module level. Keep test classes for grouping
related tests by behavior, not for fixture scoping.

```python
@pytest.fixture()
def store():
    with MyStore(sqlite3.connect(":memory:")) as s:
        yield s


class TestStoreCreateAndList:
    def test_create_and_list(self, store):
        ...
```

## One assertion purpose per test

A test method can have multiple `assert` statements if they verify the same thing (e.g.,
a dict comparison). Don't test unrelated behaviors in one method.

## Readability over DRY

Allow repetition in tests. Each test should be self-contained and readable without
jumping to shared helpers.
