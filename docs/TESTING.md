# Testing

## Running

Run the test module with pytest:

```bash
pytest tests/test_rate_limit_planner.py
```

## Policy

`tests/test_rate_limit_planner.py` imports the public API `from rate_limit_planner import Limits, Plan, PlannerError, Profile, explain, plan, plan_many` and `main` from `rate_limit_planner.__main__`. Tests assert returned `Plan` values, `PlannerError.code` values, JSON output, stdout/stderr, and CLI return codes. They do not use network access or wall-clock timing.

## Tiers

There is one test module in the provided repository. There are no separate conformance or CI-only test tiers, and no `conftest.py` is present.

## Layout

- `tests/test_rate_limit_planner.py`: all tests for the library and CLI.
