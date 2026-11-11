# trysac-rate-limit-planner

Plan safe request concurrency and pacing for LLM providers from RPM and TPM limits, average token use, and latency.

The library computes a frozen `Plan` from provider limits and an average request profile. It does not send requests or enforce limits; it returns the request rate, concurrency, interval, and the binding limit (`rpm`, `tpm`, or `concurrency`).

## Installation

```bash
pip install trysac-rate-limit-planner
```

## Usage

```python
from rate_limit_planner import Limits, Profile, plan, explain

limits = Limits(rpm=500, tpm=200_000)
profile = Profile(input_tokens=1500, output_tokens=500, latency_s=4.0)
p = plan(limits, profile)
print(p)
print(explain(p))
```

## Public API

- `Limits(rpm: int, tpm: int, max_concurrency: int | None = None)`: provider limits.
- `Profile(input_tokens: int, output_tokens: int, latency_s: float)`: average request profile.
- `Plan(requests_per_minute: int, concurrency: int, interval_s: float, bound: Literal["rpm", "tpm", "concurrency"])`: computed pacing plan.
- `plan(limits: Limits, profile: Profile, *, safety: float = 0.9) -> Plan`: computes one plan.
- `plan_many(providers: Mapping[str, Limits], profile: Profile, *, safety: float = 0.9) -> dict[str, Plan]`: computes plans for up to 100 providers and returns keys sorted.
- `explain(p: Plan) -> str`: returns a one-line human-readable description.
- `rate_limit_planner.__main__.main(argv: list[str] | None = None) -> int`: CLI entry point.

## Errors and limits

`plan`, `plan_many`, and the CLI raise or report `PlannerError` with a stable `code`:

- `invalid_limits`: `rpm`, `tpm`, or `max_concurrency` is not an `int` greater than or equal to 1; a `bool` is rejected. `plan_many` also uses this code for more than 100 providers, a non-string provider name, a name shorter than 1 or longer than 64 characters, or a value that is not a `Limits`.
- `invalid_profile`: `input_tokens` or `output_tokens` is not an `int` greater than or equal to 0, their sum is less than 1, or `latency_s` is not finite or is outside `0 < latency_s <= 3600`.
- `invalid_safety`: `safety` is not finite or is outside `0 < safety <= 1`.
- `request_too_large`: the computed allowed request rate is below 1, including when a binding `max_concurrency` cap leaves fewer than 1 request per minute.

The default `safety` is `0.9`. `max_concurrency` is optional; when it binds, `bound` is `concurrency`. The CLI accepts `--rpm`, `--tpm`, `--max-concurrency`, `--input`, `--output`, `--latency`, `--safety`, and `--explain`. It prints JSON by default, exits `0` on success, `1` on `PlannerError`, and `2` on usage errors.

## Why not a token bucket library

A token bucket library enforces a rate while requests run. This package only plans the numbers before running: it does not wait, retry, or consume tokens.

## Features

- Integer arithmetic for request and token counts, with `latency_s` used as a float.
- Little's law for concurrency: `ceil(allowed * latency_s / 60)`, at least 1.
- Optional `max_concurrency` cap.
- Input validation with `PlannerError` codes.
- No runtime dependencies; standard library only.

## Documentation

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model, and `docs/` for project, architecture, stack, and testing notes.
