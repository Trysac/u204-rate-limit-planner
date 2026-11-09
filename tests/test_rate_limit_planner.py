"""Tests for rate_limit_planner."""

from __future__ import annotations

import json
import logging
import math

import pytest

from rate_limit_planner import (
    Limits,
    Plan,
    PlannerError,
    Profile,
    explain,
    plan,
    plan_many,
)
from rate_limit_planner.__main__ import main


def test_acceptance_example_tpm_bound() -> None:
    limits = Limits(rpm=500, tpm=200_000)
    profile = Profile(input_tokens=1500, output_tokens=500, latency_s=4.0)
    result = plan(limits, profile)
    assert result == Plan(
        requests_per_minute=90,
        concurrency=6,
        interval_s=0.667,
        bound="tpm",
    )


def test_acceptance_example_rpm_bound() -> None:
    limits = Limits(rpm=60, tpm=1_000_000)
    profile = Profile(input_tokens=800, output_tokens=200, latency_s=2.0)
    result = plan(limits, profile)
    assert result.requests_per_minute == 54
    assert result.concurrency == 2
    assert result.bound == "rpm"
    assert result.interval_s == round(60 / 54, 3)


def test_acceptance_example_concurrency_bound() -> None:
    limits = Limits(rpm=500, tpm=200_000, max_concurrency=1)
    profile = Profile(input_tokens=1500, output_tokens=500, latency_s=4.0)
    result = plan(limits, profile)
    assert result.concurrency == 1
    assert result.requests_per_minute == 15
    assert result.bound == "concurrency"


def test_request_too_large() -> None:
    limits = Limits(rpm=100, tpm=100)
    profile = Profile(input_tokens=100, output_tokens=0, latency_s=1.0)
    with pytest.raises(PlannerError) as exc_info:
        plan(limits, profile)
    assert exc_info.value.code == "request_too_large"


def test_invalid_limits() -> None:
    invalid_values = [
        {"rpm": 0, "tpm": 1},
        {"rpm": 1, "tpm": -1},
        {"rpm": True, "tpm": 1},
        {"rpm": 1, "tpm": 1, "max_concurrency": 0},
        {"rpm": 1, "tpm": 1, "max_concurrency": True},
    ]
    for kwargs in invalid_values:
        with pytest.raises(PlannerError) as exc_info:
            plan(Limits(**kwargs), Profile(input_tokens=1, output_tokens=0, latency_s=1.0))
        assert exc_info.value.code == "invalid_limits"


def test_invalid_profile() -> None:
    invalid_profiles = [
        Profile(input_tokens=-1, output_tokens=0, latency_s=1.0),
        Profile(input_tokens=0, output_tokens=-1, latency_s=1.0),
        Profile(input_tokens=0, output_tokens=0, latency_s=1.0),
        Profile(input_tokens=1, output_tokens=0, latency_s=0.0),
        Profile(input_tokens=1, output_tokens=0, latency_s=3601.0),
        Profile(input_tokens=1, output_tokens=0, latency_s=math.nan),
        Profile(input_tokens=1, output_tokens=0, latency_s=math.inf),
        Profile(input_tokens=True, output_tokens=0, latency_s=1.0),
    ]
    for profile in invalid_profiles:
        with pytest.raises(PlannerError) as exc_info:
            plan(Limits(rpm=100, tpm=100), profile)
        assert exc_info.value.code == "invalid_profile"


def test_invalid_safety() -> None:
    invalid_safeties = [0.0, -0.1, 1.1, math.nan, math.inf, True]
    for safety in invalid_safeties:
        with pytest.raises(PlannerError) as exc_info:
            plan(
                Limits(rpm=100, tpm=100),
                Profile(input_tokens=1, output_tokens=0, latency_s=1.0),
                safety=safety,
            )
        assert exc_info.value.code == "invalid_safety"


def test_safety_exactly_one() -> None:
    limits = Limits(rpm=10, tpm=100)
    profile = Profile(input_tokens=10, output_tokens=0, latency_s=1.0)
    result = plan(limits, profile, safety=1.0)
    assert result.requests_per_minute == 10  # min(10,10)
    assert result.bound == "rpm"


def test_max_concurrency_not_binding() -> None:
    limits = Limits(rpm=100, tpm=100_000, max_concurrency=5)
    profile = Profile(input_tokens=10, output_tokens=0, latency_s=1.0)
    result = plan(limits, profile, safety=0.9)
    # concurrency = ceil(90 * 1 / 60) = 2, less than max_concurrency=5
    assert result.concurrency == 2
    assert result.bound != "concurrency"
    assert result.requests_per_minute == 90


def test_rounding_of_interval() -> None:
    limits = Limits(rpm=7, tpm=1_000_000)
    profile = Profile(input_tokens=1, output_tokens=0, latency_s=1.0)
    result = plan(limits, profile, safety=1.0)
    assert result.requests_per_minute == 7
    assert result.interval_s == round(60 / 7, 3)


def test_max_concurrency_binding_below_one_rpm() -> None:
    limits = Limits(rpm=500, tpm=200_000, max_concurrency=1)
    profile = Profile(input_tokens=1500, output_tokens=500, latency_s=61.0)
    with pytest.raises(PlannerError) as exc_info:
        plan(limits, profile)
    assert exc_info.value.code == "request_too_large"


def test_cli_slow_latency_with_concurrency_cap_returns_1(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = [
        "--rpm",
        "500",
        "--tpm",
        "200000",
        "--max-concurrency",
        "1",
        "--input",
        "1500",
        "--output",
        "500",
        "--latency",
        "120",
    ]
    ret = main(argv)
    captured = capsys.readouterr()
    assert ret == 1
    assert "request_too_large" in captured.err
    assert "Traceback" not in captured.err


def test_plan_many_validates_profile_even_when_empty() -> None:
    with pytest.raises(PlannerError) as exc_info:
        plan_many({}, Profile(input_tokens=0, output_tokens=0, latency_s=1.0))
    assert exc_info.value.code == "invalid_profile"


def test_plan_many_validates_safety_even_when_empty() -> None:
    with pytest.raises(PlannerError) as exc_info:
        plan_many({}, Profile(input_tokens=1, output_tokens=0, latency_s=1.0), safety=1.5)
    assert exc_info.value.code == "invalid_safety"


def test_plan_many_sorted_and_matches_individual() -> None:
    providers = {
        "b": Limits(rpm=60, tpm=1_000_000),
        "a": Limits(rpm=500, tpm=200_000),
    }
    profile = Profile(input_tokens=1500, output_tokens=500, latency_s=4.0)
    result = plan_many(providers, profile)
    assert list(result.keys()) == ["a", "b"]
    assert result["a"] == plan(providers["a"], profile)
    assert result["b"] == plan(providers["b"], profile)


def test_plan_many_too_many_providers() -> None:
    providers = {str(i): Limits(rpm=100, tpm=100) for i in range(101)}
    with pytest.raises(PlannerError) as exc_info:
        plan_many(providers, Profile(input_tokens=1, output_tokens=0, latency_s=1.0))
    assert exc_info.value.code == "invalid_limits"


def test_plan_many_invalid_name_length() -> None:
    for name in ["", "a" * 65]:
        providers = {name: Limits(rpm=100, tpm=100)}
        with pytest.raises(PlannerError) as exc_info:
            plan_many(providers, Profile(input_tokens=1, output_tokens=0, latency_s=1.0))
        assert exc_info.value.code == "invalid_limits"


def test_plan_many_non_string_name() -> None:
    with pytest.raises(PlannerError) as exc_info:
        plan_many(
            {123: Limits(rpm=100, tpm=100)},
            Profile(input_tokens=1, output_tokens=0, latency_s=1.0),
        )
    assert exc_info.value.code == "invalid_limits"


def test_plan_many_non_limits_value() -> None:
    with pytest.raises(PlannerError) as exc_info:
        plan_many(
            {"a": "not limits"},
            Profile(input_tokens=1, output_tokens=0, latency_s=1.0),
        )
    assert exc_info.value.code == "invalid_limits"


def test_explain_acceptance() -> None:
    plan_obj = Plan(
        requests_per_minute=90,
        concurrency=6,
        interval_s=0.667,
        bound="tpm",
    )
    assert (
        explain(plan_obj)
        == "90 requests/min with 6 in flight (bound by tpm), one request every 0.667 s"
    )


def test_cli_success_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = [
        "--rpm",
        "500",
        "--tpm",
        "200000",
        "--input",
        "1500",
        "--output",
        "500",
        "--latency",
        "4",
    ]
    monkeypatch.setattr("sys.argv", ["prog", *argv])
    ret = main(argv)
    captured = capsys.readouterr()
    assert ret == 0
    expected = {
        "requests_per_minute": 90,
        "concurrency": 6,
        "interval_s": 0.667,
        "bound": "tpm",
    }
    assert json.loads(captured.out) == expected
    assert captured.err == ""


def test_cli_missing_rpm_returns_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = [
        "--tpm",
        "200000",
        "--input",
        "1500",
        "--output",
        "500",
        "--latency",
        "4",
    ]
    ret = main(argv)
    captured = capsys.readouterr()
    assert ret == 2
    assert "--rpm" in captured.err


def test_cli_request_too_large_returns_1(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = [
        "--rpm",
        "100",
        "--tpm",
        "100",
        "--input",
        "100",
        "--output",
        "0",
        "--latency",
        "1",
    ]
    ret = main(argv)
    captured = capsys.readouterr()
    assert ret == 1
    assert "request_too_large" in captured.err


def test_cli_explain(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    argv = [
        "--rpm",
        "500",
        "--tpm",
        "200000",
        "--input",
        "1500",
        "--output",
        "500",
        "--latency",
        "4",
        "--explain",
    ]
    ret = main(argv)
    captured = capsys.readouterr()
    assert ret == 0
    assert (
        captured.out.strip()
        == "90 requests/min with 6 in flight (bound by tpm), one request every 0.667 s"
    )


def test_logger_has_null_handler() -> None:
    logger = logging.getLogger("rate_limit_planner")
    assert any(isinstance(h, logging.NullHandler) for h in logger.handlers)
