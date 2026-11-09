# rate-limit-planner

[![PyPI version](https://img.shields.io/pypi/v/trysac-rate-limit-planner)](https://pypi.org/project/trysac-rate-limit-planner/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-rate-limit-planner)](LICENSE)
[![CI](https://github.com/Trysac/u204-rate-limit-planner/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u204-rate-limit-planner/actions/workflows/ci.yml)

Plan safe request concurrency and pacing for LLM providers from their RPM and TPM limits, average token use and latency

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-rate-limit-planner
# or
uv add trysac-rate-limit-planner
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import rate_limit_planner

# normalize() trims surrounding whitespace and lower-cases the text.
print(rate_limit_planner.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    rate_limit_planner.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
