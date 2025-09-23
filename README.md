# Architecture Diagrams (C4 + Structurizr DSL)

This repository provides a small toolkit to define C4-style architecture models and materialize them into Structurizr DSL, plus a few helpers to run Structurizr Lite locally.


> **Note:**  
> This project has been created with the support of large language models (LLMs).  
> As a result, some code may reflect an iterative or "vibe coding" style.  
> The codebase will be gradually cleaned up and refactored for clarity and maintainability.

It includes an example project under `projects/banking` to demonstrate how to structure models and views.

The CLI entrypoint is `architecture-diagrams`:

```
uv run architecture-diagrams --help
```

## Setup

This repository uses the `uv` package manager.

To start using this repository, first install `uv`:

```
pip install uv
```

Once `uv` is installed globally, you start using the project by running the CLI script. It will 
automatically install all the requirements before execution:

```
uv run architecture-diagrams --help
## Note on immutability

Earlier experimental immutable model duplicates (I* types) were removed. The primary C4 model remains the source of truth, keeping the user-facing API unchanged and overlays/tagging operating in-place.
```

## Building (optional)

You can build a wheel/sdist if you plan to publish:

```
uv build
```

## Decoupled views and tags

The C4 model and the views are decoupled:
- Model builders live under `projects/<project>/models/**`.
- View definitions live under `projects/<project>/views/**` and return `List[ViewSpec]` via a module-level `get_views()`.

What this gives us:
- View sets can be selected independently by name, tag, or module (subject root), without touching the model.
- We can maintain legacy semantics (SmartView, relationship filters) while evolving views safely.

### Where things live
- Model (systems, containers, relationships): `projects/<project>/models/...`.
- Views (System Landscape/Context/Container): `projects/<project>/views/*.py`.
- Orchestrator & exporter: `architecture_diagrams/orchestrator/*` and `architecture_diagrams/adapter/pystructurizr_export.py`.

### ViewSpec in a nutshell
Each view file defines a `get_views()` that returns `List[ViewSpec]`:

Contract:
- Inputs: name/key/view_type/subject, optional includes/excludes, tags, and filters
- Output: normalized Structurizr DSL via the CLI exporter
- Error modes: name mismatches in filters are ignored with no crash; selection with unknown names/tags/modules yields no views
- Success: selected views are built and only those are emitted into the DSL

Common fields:
- `key`: stable identifier for the view
- `name`, `description`
- `view_type`: one of System Landscape, System Context, Container (see `ViewType`)
- `subject`: subject system or container (e.g., `"connect"` or `"connect/care-navigation-bff"`)
- `tags`: any of `{default, td}` (project-specific tags)
- `includes`: optional; when omitted, a single wildcard include is injected by the exporter so the subject and neighbors show up
- `element_excludes_names`: optional list of element display names to hide from the view (e.g., queue components)
- `filters`: relationship-level filters that fine-tune edges, compatible with legacy semantics

### Relationship filtering
We preserve legacy SmartView filtering behavior. Two ways to express filters:
- Name-based relationship filters (preferred for parity):
	- `ExcludeRelByName` (aliased as `XRel` in many view files) supports:
		- `from_name`: element display name (system or container)
		- `to_name`: optional target display name; when omitted, excludes all outgoing relationships from `from_name`
		- `but_include_names`: list of display names that are re-included explicitly (deterministic and order-stable)
	- Example: `XRel(from_name="assess", to_name=None, but_include_names=["Mobile"])`
		- Excludes all relationships from Assess, except those into Mobile.
- Legacy RelationshipFilter stashing:
	- ViewSpec stores classic `RelationshipFilter` instances and the exporter translates these into deterministic name-based includes/excludes in the DSL.

Edge cases handled by the exporter:
- Inject single wildcard include where `includes` are omitted (no duplicates)
- Preserve legacy include/subject semantics per view type
- Apply element-level excludes as `exclude <element>` in DSL
- Reorder relationships deterministically for stable diffs
- Emit only selected views; no prune-to-views by default (so broader context remains visible)

### Selecting views: names, tags, and modules
You can pick views by name, by tag, or by module (the subject root, a.k.a. SYSTEM_KEY).

Discovery:
- List all views with names and tags:
	- `uv run architecture-diagrams list-views`
- List available modules (subject roots):
	- `uv run architecture-diagrams list-modules --project banking`

Generate DSLs:
- By tag (all defaults):
	- `uv run architecture-diagrams generate --project banking --tags default --output workspace.dsl`
- By explicit names (mix-and-match):
	- `uv run architecture-diagrams generate --project banking --views PaymentsContainer BankingSystemContext --output workspace.dsl`
- By modules (no need to enumerate view names):
	- `uv run architecture-diagrams generate --project banking --modules payments,channels --output workspace.dsl`

Notes:
- By default we don’t prune the model to elements in views. Use `--prune-to-views` if you need a trimmed DSL.
- diag_c4 legacy files remain read-only for parity. All new view work happens in `projects/<project>/views/**`.

### Structurizr Lite workflow
You can build DSLs on the fly and run Structurizr Lite locally.

- Start Lite mounting a generated DSL for a module:
	- `uv run architecture-diagrams lite start --project banking --modules payments`
- Or generate first, then start:
	- `uv run architecture-diagrams generate --project banking --modules payments --output .structurizr/workspace.dsl`
	- `uv run architecture-diagrams lite start`
- Stop Lite:
	- `uv run architecture-diagrams lite stop`

### Examples in views
- Minimal defaults with TD variants curated via filters in `projects/banking/views/*_views.py`:
	- Default views omit includes for a broader context.
	- TD views add filters to re-include only specific edges.

For a deeper dive into the architecture and normalization rules, see `docs/DESIGN_NOTES.md`.