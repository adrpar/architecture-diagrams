# Architecture diagrams: design notes

This document captures the architecture and design decisions behind the decoupled model/view approach and the tooling around it.

## Goals
- Views are defined independently from the model and can evolve without touching the model code.
- Maintain parity with legacy `diag_c4` SmartViews and RelationshipFilter semantics.
- Provide deterministic, normalized Structurizr DSL output suitable for review and diffing.
- Enable selection by names, tags, and modules (subject roots) via CLI.

## High-level architecture
- Model layer
  - Builders and legacy parity live under `projects/<project>/models/**`.
- View layer
  - `projects/<project>/views/**` Python modules exporting `get_views() -> List[ViewSpec]`.
- Orchestrator
  - `architecture_diagrams/orchestrator/*` composes model + selected views and produces a Workspace.
  - Selection by names, tags, or modules (subject root).
- Exporter
  - `architecture_diagrams/adapter/pystructurizr_export.py` renders to Structurizr DSL with normalization.

## ViewSpec schema (summary)
- `key`, `name`, `description`, `view_type`, `subject`
- `tags`: e.g. `default`, `td` (project-specific, see `projects/<project>/views/*`)
- `includes`: optional. When omitted, exporter injects a single wildcard include appropriate for the view type.
- `element_excludes_names`: optional list of element display names to hide (mapped to `exclude <element>` in DSL).
- `filters`: optional list of relationship filters; supports legacy compatibility and name-based filtering.

### Filters
- Name-based relationship filters (preferred for parity and determinism):
  - `ExcludeRelByName` (aliased as `XRel` in view files) with fields:
    - `from_name: str` – display name to match (system or container)
    - `to_name: Optional[str]` – when None, excludes all outgoing edges from `from_name`
    - `but_include_names: list[str]` – re-include subset by display name
- Legacy stashing: ViewSpec can carry the classic `RelationshipFilter` objects; exporter converts them to deterministic includes/excludes in DSL.

## Normalization rules (exporter)
- Inject a single wildcard include if `includes` is empty/omitted, avoiding duplicates.
- Respect include/subject semantics per view type (System Landscape/Context/Container) as in legacy.
- Reorder relationships deterministically for stable diffs.
- Apply `element_excludes_names` as `exclude` lines in DSL.
- Emit only selected views. By default do NOT prune model elements outside the selected views (preserve context).

## Modules (SYSTEM_KEY)
- Subject roots (e.g., `connect`, `assess`, `mobile`) are discoverable from views.
- CLI selection by modules avoids enumerating view keys.
- `uv run architecture-diagrams list-modules` displays the available module keys.

## CLI workflows
- List views: `uv run architecture-diagrams list-views`
- List modules: `uv run architecture-diagrams list-modules`
- Generate DSL by tag: `uv run architecture-diagrams generate --tags default --output workspace.dsl`
- Generate DSL by names: `uv run architecture-diagrams generate --views ConnectSystemContext AssessContainer --output workspace.dsl`
- Generate DSL by modules: `uv run architecture-diagrams generate --modules connect,assess --output workspace.dsl`
- Start Structurizr Lite with a generated workspace: `uv run architecture-diagrams lite start` (uses .structurizr/workspace.dsl)

## Legacy parity patterns
- Minimal defaults: default views usually omit explicit `includes`. The exporter injects a wildcard to keep helpful context.
- TD variants: use `XRel` filters to mirror classic SmartView `exclude from X except to Subject` behavior.
- Element-level excludes: hide noisy queue elements or non-essential infra by name.
- Name normalization: filter matching is tolerant of spaces, dashes, and capitalization differences between model display names and filter names.

## Troubleshooting & tips
- A relationship you expect is missing:
  - Check TD filters (`XRel`) aren’t excluding it; add `but_include_names=["Target Name"]` if needed.
- Too many elements in a view:
  - Add `element_excludes_names=["Noisy Component"]` or a targeted `XRel`.
- A filter name doesn’t seem to match:
  - Confirm the display name in the model (system or container) and adjust the filter string; normalization helps, but exact is best.
- Only some views appear in the DSL:
  - Ensure your selection matches (names/tags/modules). The exporter emits only selected views by design.

## Future enhancements
- Optional pruning strategies configurable per CLI invocation.
- Presets for TD view conventions across modules.
- Additional validators to check for name mismatches between filters and model.
