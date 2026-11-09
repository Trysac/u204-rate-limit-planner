# Security notes

## Threat model

The package is a pure library with no network, filesystem, subprocess, or runtime dependencies. It computes `Plan` values from caller-supplied dataclasses.

Defended:

- Invalid structured input: `Limits`, `Profile`, and `safety` validation raises `PlannerError` with `code` in `invalid_limits`, `invalid_profile`, or `invalid_safety`.
- Oversized request or unplannable rate: `plan` raises `PlannerError("request_too_large")` when the allowed request rate is below 1.
- Oversized provider maps: `plan_many` raises `PlannerError("invalid_limits")` with more than 100 providers, names outside 1–64 characters, non-string names, or non-`Limits` values.
- Logging side effects: the module logger uses `logging.NullHandler`; the library never configures logging, prints, or exits.
- Code execution: the library has no `eval`, `exec`, deserialization, shell calls, or file/network access.

Not defended:

- Live enforcement: `plan` and `plan_many` do not wait, retry, consume tokens, or block requests.
- Token counting: callers must supply average `input_tokens` and `output_tokens`.
- Provider headers: the package has no HTTP client and does not read `Retry-After` or other headers.
- Misuse of the result: callers must apply `requests_per_minute`, `concurrency`, and `interval_s` themselves.
- Input limits above the code's checks: `latency_s` is capped at 3600 seconds and `safety` at 1; values outside those bounds are rejected, not clamped.

## Publishing

The code does not publish artifacts, perform network access, or store credentials. Release tooling is outside this package.
