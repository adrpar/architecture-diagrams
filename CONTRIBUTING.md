# Contributing

Thanks for considering contributing!

## Getting started

- Prerequisites: Python 3.12+, [uv](https://docs.astral.sh/uv/) installed
- Install dependencies on first run:
  - `uv run architecture-diagrams --help`

## Dev loop

- Run tests: `uv run pytest -q`
- Type-check: `uv run mypy`
- Lint/format (if using ruff): `uv run ruff check .` and `uv run ruff format .`

## Submitting changes

- Fork and create a feature branch
- Add/adjust tests when changing behavior
- Ensure CI is green (tests, typing, lint)
- Update docs/README when needed

## Code of Conduct

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
