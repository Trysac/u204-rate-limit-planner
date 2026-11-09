# Architecture

## Purpose

`trysac-rate-limit-planner` is a stdlib-only Python library that computes a `Plan` from provider limits and an average request profile. It plans numbers; it does not enforce limits.

## Shape

```text
caller code --> rate_limit_planner.__init__ (public API)
                    |
                    +-- plan() / plan_many() / explain()
                    |
                    +-- rate_limit_planner.__main__ (argument parsing and CLI output)
```

- **Public API**: `Limits`, `Plan`, `PlannerError`, `Profile`, `explain`, `plan`, and `plan_many`; these names are in `__all__`.
- **Errors**: invalid input raises `PlannerError` with `code` set to `invalid_limits`, `invalid_profile`, `invalid_safety`, or `request_too_large`. The library does not raise `ValueError` or `TypeError` for these validations.
- **Side effects**: none in the library. It does not perform network or filesystem I/O, configure logging, print, or exit. The CLI handles printing and exit codes.
- **Dependencies**: Python standard library only. The package includes `py.typed`.

## Quality contract

The code in `src/rate_limit_planner` is covered by `tests/test_rate_limit_planner.py`, which checks the public API, validation codes, CLI return codes, and stdout/stderr behavior. No separate quality-gate script is present in the provided repository files.

## Decisions

No architecture decision records are included in the provided repository files.
