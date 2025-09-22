# View Specs, Tags, and CLI

This project decouples views from the C4 model. Views are defined as independent "spec" modules and discovered via convention.

## Directory conventions

- Models (C4 builders): `projects/<project>/models/*.py`
  - Root builder: `projects/<project>/models/system_landscape.py` composes all discovered C4 modules.
  - Two-phase registration is handled internally; modules can define `define_*` and `link_*` functions.
- Views (independent specs): `projects/<project>/views/*_views.py`
  - Each module exports `get_views() -> list[ViewSpec]` returning view specifications.
  - Do not modify files under legacy directories; use projects/<project>/models and views.

## ViewSpec

Fields:
- key: unique view key
- name: display name (used as view title)
- view_type: one of SystemLandscape, SystemContext, Container, Component
- description: human-readable description
- tags: set of tags for selection, e.g., `{DEFAULT}`, `{TD}`
- includes/excludes: element selectors by name, or `person:Name`, or callables; relationship filters are accepted for smart views
- subject: required for non-landscape views, e.g., `System` (context) or `System/Container` (container/component)
- smart: mark SystemLandscape view as smart (includes `*`)

Tag constants can live in `projects/<project>/views/tags.py` if desired.

## Selecting views

Use tags and/or names to select a subset of views for generation:
- Tags: `DEFAULT`, `TD`
- Names: any subset of `ViewSpec.key` values

## CLI usage

- List views (for discoverability):
  - `uv run architecture-diagrams list-views`
- Generate DSL for selected views:
  - `uv run architecture-diagrams generate --tag default`
  - `uv run architecture-diagrams generate --name AssessContainer --name ConnectSystemContext`
- Run Structurizr Lite with on-the-fly generation:
  - `uv run architecture-diagrams lite --tag td`

## Adding a new view

1. Create a new file under `projects/<project>/views/xyz_views.py`.
2. Export a `get_views()` function that returns one or more `ViewSpec` instances.
3. Use `subject="System"` for system context or `subject="System/Container"` for container views.
4. Assign `tags={DEFAULT}` or `tags={TD}` (or both) as needed.
5. Test: `uv run pytest -q`.

## Parity and regression

- We maintain test coverage to ensure the orchestrator and views produce the same view set as legacy builders for `default` and `td` tags.
- The adapter creates the correct pystructurizr view types by providing the required element context for non-landscape views.

