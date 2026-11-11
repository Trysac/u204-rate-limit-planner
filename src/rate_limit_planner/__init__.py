"""Plan safe request concurrency and pacing for LLM providers.

This module computes a :class:`Plan` from provider limits, average token usage
and latency.  It does not enforce limits; it only plans numbers.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

__all__ = [
    "Limits",
    "Plan",
    "PlannerError",
    "Profile",
    "explain",
    "plan",
    "plan_many",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class PlannerError(Exception):
    """Base error for the rate-limit planner.

    Attributes:
        code: A stable machine-readable code describing the error.
    """

    def __init__(
        self,
        code: Literal[
            "invalid_limits",
            "invalid_profile",
            "invalid_safety",
            "request_too_large",
        ],
    ) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Limits:
    """Provider rate limits.

    Args:
        rpm: Maximum requests per minute.
        tpm: Maximum tokens per minute.
        max_concurrency: Optional hard cap on concurrent requests.
    """

    rpm: int
    tpm: int
    max_concurrency: int | None = None


@dataclass(frozen=True)
class Profile:
    """Average request profile.

    Args:
        input_tokens: Average number of input tokens per request.
        output_tokens: Average number of output tokens per request.
        latency_s: Average end-to-end latency in seconds.
    """

    input_tokens: int
    output_tokens: int
    latency_s: float


@dataclass(frozen=True)
class Plan:
    """Computed pacing plan.

    Args:
        requests_per_minute: Safe number of requests per minute.
        concurrency: Recommended number of concurrent in-flight requests.
        interval_s: Time between consecutive requests in seconds.
        bound: The limiting factor: ``rpm``, ``tpm`` or ``concurrency``.
    """

    requests_per_minute: int
    concurrency: int
    interval_s: float
    bound: Literal["rpm", "tpm", "concurrency"]


def _validate_limits(limits: Limits) -> None:
    """Validate a Limits instance."""
    if not isinstance(limits.rpm, int) or isinstance(limits.rpm, bool) or limits.rpm < 1:
        raise PlannerError("invalid_limits")
    if not isinstance(limits.tpm, int) or isinstance(limits.tpm, bool) or limits.tpm < 1:
        raise PlannerError("invalid_limits")
    if limits.max_concurrency is not None and (
        not isinstance(limits.max_concurrency, int)
        or isinstance(limits.max_concurrency, bool)
        or limits.max_concurrency < 1
    ):
        raise PlannerError("invalid_limits")


def _validate_profile(profile: Profile) -> None:
    """Validate a Profile instance."""
    if (
        not isinstance(profile.input_tokens, int)
        or isinstance(profile.input_tokens, bool)
        or profile.input_tokens < 0
    ):
        raise PlannerError("invalid_profile")
    if (
        not isinstance(profile.output_tokens, int)
        or isinstance(profile.output_tokens, bool)
        or profile.output_tokens < 0
    ):
        raise PlannerError("invalid_profile")
    if profile.input_tokens + profile.output_tokens < 1:
        raise PlannerError("invalid_profile")
    if (
        not isinstance(profile.latency_s, (int, float))
        or isinstance(profile.latency_s, bool)
        or not math.isfinite(profile.latency_s)
        or not 0 < profile.latency_s <= 3600
    ):
        raise PlannerError("invalid_profile")


def _validate_safety(safety: float) -> None:
    """Validate the safety factor."""
    if (
        not isinstance(safety, (int, float))
        or isinstance(safety, bool)
        or not math.isfinite(safety)
        or not 0 < safety <= 1
    ):
        raise PlannerError("invalid_safety")


def plan(limits: Limits, profile: Profile, *, safety: float = 0.9) -> Plan:
    """Compute a safe request plan.

    Args:
        limits: Provider rate limits.
        profile: Average request profile.
        safety: Fraction of the limits to use (default 0.9).

    Returns:
        A :class:`Plan` with the recommended pacing.

    Raises:
        PlannerError: If any input is invalid or the token usage exceeds
            the safe token limit.
    """
    _validate_limits(limits)
    _validate_profile(profile)
    _validate_safety(safety)

    tokens = profile.input_tokens + profile.output_tokens
    rpm_cap = math.floor(limits.rpm * safety)
    tpm_allowed = math.floor(limits.tpm * safety)
    tpm_req_cap = tpm_allowed // tokens
    allowed = min(rpm_cap, tpm_req_cap)
    if allowed < 1:
        raise PlannerError("request_too_large")

    bound: Literal["rpm", "tpm", "concurrency"] = "tpm" if tpm_req_cap < rpm_cap else "rpm"
    concurrency = max(1, math.ceil(allowed * profile.latency_s / 60))
    requests_per_minute = allowed

    if limits.max_concurrency is not None and concurrency > limits.max_concurrency:
        concurrency = limits.max_concurrency
        rpm_from_concurrency = math.floor(limits.max_concurrency * 60 / profile.latency_s)
        requests_per_minute = min(allowed, rpm_from_concurrency)
        bound = "concurrency"
        if requests_per_minute < 1:
            raise PlannerError("request_too_large")

    interval_s = round(60 / requests_per_minute, 3)
    return Plan(
        requests_per_minute=requests_per_minute,
        concurrency=concurrency,
        interval_s=interval_s,
        bound=bound,
    )


def plan_many(
    providers: Mapping[str, Limits],
    profile: Profile,
    *,
    safety: float = 0.9,
) -> dict[str, Plan]:
    """Compute plans for multiple providers.

    Args:
        providers: Mapping of provider name to its limits.
        profile: Shared average request profile.
        safety: Safety factor.

    Returns:
        Dictionary mapping provider names to their plans, with keys sorted.

    Raises:
        PlannerError: If the mapping has too many providers, a provider name
            is invalid, or any limits are invalid.
    """
    _validate_profile(profile)
    _validate_safety(safety)

    if len(providers) > 100:
        raise PlannerError("invalid_limits")
    for name in providers:
        if not isinstance(name, str) or not 1 <= len(name) <= 64:
            raise PlannerError("invalid_limits")
        if not isinstance(providers[name], Limits):
            raise PlannerError("invalid_limits")

    result: dict[str, Plan] = {}
    for name in sorted(providers):
        result[name] = plan(providers[name], profile, safety=safety)
    return result


def explain(plan: Plan) -> str:
    """Return a human-readable explanation of a plan.

    Args:
        plan: A computed plan.

    Returns:
        A string like ``"90 requests/min with 6 in flight (bound by tpm),
        one request every 0.667 s"``.
    """
    return (
        f"{plan.requests_per_minute} requests/min with {plan.concurrency} in flight "
        f"(bound by {plan.bound}), one request every {plan.interval_s} s"
    )
