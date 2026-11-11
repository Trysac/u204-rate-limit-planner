# Stack

## Used

| Tool | Why |
|---|---|
| Python >= 3.10 | The package uses PEP 604 union syntax such as `int | None` and built-in generics. |
| Python standard library | `dataclasses`, `logging`, `math`, `argparse`, `json`, `collections.abc`, and `typing`; no runtime dependencies. |
| pytest | `tests/test_rate_limit_planner.py` uses `pytest.raises`, `monkeypatch`, and `capsys`. |

## Discarded

| Tool | Why not |
|---|---|
| Additional runtime dependencies | The package is standard-library-only and the specification lists no allowed dependencies. |
