# Use pure functions and dataclasses for planning

Status: accepted (generated, pending human review)

## Context

The library must compute request plans from numeric inputs without any side effects or external services.

## Decision

Implement planning as pure functions operating on frozen dataclasses. All validation raises a single `PlannerError` with a stable code. The CLI is a thin wrapper around these functions.

## Consequences

The core is trivially testable and deterministic. No global state or I/O. Users can integrate the planner into any runtime. Logging is disabled by default via a `NullHandler`.
