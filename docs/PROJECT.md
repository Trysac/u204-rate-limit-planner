# Project record

## Objective

Plan safe request concurrency and pacing for LLM providers from their RPM and TPM limits, average token use, and latency.

## Scope

In scope: the public API in `rate_limit_planner` — `Limits`, `Profile`, `Plan`, `PlannerError`, `plan`, `plan_many`, `explain` — and the CLI in `rate_limit_planner.__main__`.

Out of scope: live rate limiting, token counting, and reading provider headers. The package computes planning numbers; it does not enforce them.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays pending measurement.

| Metric | Value |
|---|---|
| Tokens (input / output) | 515747 / 38709 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.0583 |

## Factory run u204 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | deepseek-v4-pro | yes | 4820 | 10297 | 0 | 0 | 0.0236 |
| fix-1 | deepseek-flash | no | 8775 | 1410 | 0 | 36480 | 0.0023 |
| audit | deepseek-flash | no | 35883 | 15615 | 0 | 337280 | 0.0158 |
| fix-2 | deepseek-flash | no | 6202 | 1107 | 0 | 27264 | 0.0017 |
| docs | deepseek-flash | no | 59043 | 10280 | 0 | 0 | 0.0150 |

Total: $0.0583. Prices: deepseek line, as measured by its adapter.
