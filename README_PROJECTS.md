# Projects layout and usage

This repository supports multiple projects under the repository root `projects/<project>` only. Each project has independent models and views.

- Models: `projects/<project>/models` — modules `*_c4.py` must export `define_<name>(model)` and optionally `link_<name>(model)`
- Views: `projects/<project>/views` — modules export `get_views()` which returns a list of `ViewSpec`
- Optional manifest: `projects/<project>/project.toml` — allows overriding the workspace name. Example:

```
workspace_name = "Banking"
```

## Creating project variants (overlays)

Often you want to propose or explore an architectural evolution without copying the entire project. A simple, scalable way is to create a new project that reuses most of the base project and applies a small overlay (mutation) in its own `models/system_landscape.py`.

Example: Banking variant that replaces Kafka with a Redis Queue

1) Create a new project `projects/banking_redis/` with:
  - `project.toml` to give it a distinct workspace name
  - `models/system_landscape.py` that imports the base builder and then applies changes
  - optionally `views/*.py` with views focused on the changed area

```
projects/
  banking/
   models/
    ...
  banking_redis/
   project.toml
   models/
    system_landscape.py  # delegates to base and mutates
   views/
    eventing_variants.py # optional, add views highlighting the change
```

Minimal variant builder pattern (delegation + mutation):

```python
from typing import Optional
from architecture_diagrams.c4.system_landscape import SystemLandscape

def build(model: Optional[SystemLandscape] = None) -> SystemLandscape:
   from projects.banking.models.system_landscape import build as base_build
   model = base_build(model)

   # apply minimal changes here (e.g., replace containers, rewire relationships)
   eventing = model.get_system("Eventing")
   redis = eventing.add_container("Redis Queue", "Queue for events", technology="Redis Streams")

   try:
      kafka = model.get_container("Eventing", "Kafka")
   except Exception:
      kafka = None
   if kafka:
      for rel in list(model.relationships):
        if rel.source is kafka:
           rel.source = redis
        if rel.destination is kafka:
           rel.destination = redis
      # hide Kafka from the model by removing it
      new_containers = [c for c in eventing.containers if c.name != "Kafka"]
      eventing._containers.clear()  # type: ignore[attr-defined]
      for c in new_containers:
        eventing._containers[c.name] = c  # type: ignore[attr-defined]

   return model
```

CLI usage:

- Generate DSL for the variant:
  - `uv run arch-diags generate --project banking_redis --output .structurizr/workspace.dsl`

This overlay approach avoids duplication and keeps most entities untouched.

### Recommended practices for overlays

- Keep mutations local and explicit: add/remove containers, retarget relationships, update tags.
- Use `SystemLandscape.replace_container(system, old, new, description=..., technology=..., tag_new=..., tag_old=..., remove_old=True)` to replace technology or move endpoints without duplicating modules.
- Add variant-specific views to highlight the change; use `filters` to restrict relationships for clarity.
- Use `project.toml` to give the variant a distinct workspace name.
- Avoid re-defining base `*_c4.py` files; prefer post-build mutations in the variant's `system_landscape.py`.

### Enhancements to make overlays easier

These are improvements we can add to reduce boilerplate and make overlays first-class:

1) Project manifest inheritance and extensions (supported)
  - Set `extends = "<base>"` in `project.toml` to indicate a base project.
  - The orchestrator builds the base project first, then composes the derived project's builders on top.

2) Overlay hooks in the orchestrator (supported)
3) View inheritance (supported)
   - You can extend a base view by key using `extends_key` in a derived project's `ViewSpec`.
   - Merging rules:
     - name, view_type, description, subject: derived overrides if set; otherwise inherited
     - tags: union (base ∪ derived)
     - includes/excludes/filters: concatenated (base first, then derived)
     - smart: derived True overrides; otherwise base value
   - Example:
     ```python
     ViewSpec(
         key="EventingOverviewRedisInherited",
         view_type=ViewType.SYSTEM_LANDSCAPE,
         extends_key="EventingOverview",
         includes=["Eventing/Redis Queue"],
         filters=[IncludeRelByName(from_name="Core Banking/Ledger Service", to_name="Eventing/Redis Queue")],
         smart=True,
     )
     ```

  - Put `apply(model)` functions in `projects/<variant>/models/overlays/*.py`.
  - Build order: base builders -> derived builders -> overlay apply() -> views (base + derived).

3) View inheritance/override
  - Allow variant views to reference base views by key and declare `extends_key = "EventingOverview"` to auto-copy includes and tweak filters/excludes.
  - Provide a small helper to clone/modify a `ViewSpec` from code.

4) First-class element replace helper
  - Add utility: `replace_container(model, system_name, old_name, new_name, new_desc, new_tech)` that rewires relationships and handles container dict updates safely.

5) Styling for deltas
  - Add default styles/tags for `proposed`, `deprecated` and surface legend in views to signal changes.

6) External overlays via `--project-path`
  - Already partially supported; we can enhance loader to accept both base project and overlay path(s) and merge views/builders accordingly.

If you're interested, we can implement items (1), (2), and (4) with minimal changes to the orchestrator and add a tiny helper module.


## CLI

Always use uv.

- Generate DSL for a project:

```
uv run architecture-diagrams generate --project banking --output workspace.dsl
```

- List views for a project:

```
uv run architecture-diagrams list-views --project banking
```

- List modules inferred from views (subjects):

```
uv run architecture-diagrams list-modules --project banking
```

- Selective generation by names, tags, or modules:

```
uv run architecture-diagrams generate --project banking --views ReportingDataLineage,BankingDataFlows
uv run architecture-diagrams generate --project banking --tags analytics,channels
uv run architecture-diagrams generate --project banking --modules payments,channels
```

## Name-based relationship filters

Views can add filters that generate `include A->B` or `exclude A->B` lines in the DSL by referring to elements by display names, including nested forms like `System/Container`.
Use `IncludeRelByName` and `ExcludeRelByName` in `architecture_diagrams.orchestrator.specs`.

Examples:

- Only show ETL pulls:

```python
ViewSpec(
  key="ReportingDataLineage",
  view_type=ViewType.CONTAINER,
  subject="Reporting/ETL Job",
  includes=["Reporting/ETL Job","Core Banking/Accounts Service","Payments/Payments API"],
  filters=[
    IncludeRelByName(from_name="Reporting/ETL Job", to_name="Core Banking/Accounts Service"),
    IncludeRelByName(from_name="Reporting/ETL Job", to_name="Payments/Payments API"),
  ],
)
```

- Exclude everything then but-include specific cross-references:

```python
ViewSpec(
  key="NotificationsContainer",
  view_type=ViewType.CONTAINER,
  subject="Notifications/Event Router",
  includes=["Notifications/Event Router","Payments/Payments API","Email Provider/SMTP"],
  filters=[
    ExcludeRelByName(from_name="*", to_name="*", but_include_names=[
      "Payments/Payments API",
      "Email Provider/SMTP",
    ])
  ],
)
```

## Migration notes

- Place all project content under root-level `projects/<project>/{models,views}`.
- If you have older modules, move them to the `projects` layout and ensure `SYSTEM_KEY` matches the display name created by `define_<name>()`.

### Moving projects to the repository root

All projects must live under `projects/<project>`.

Migration from in-package layout:
  - Update imports to use `from projects.<project>...`
- Add `projects/<project>/project.toml` with `workspace_name = "Your Name"` if you want a custom name
- Run: `uv run architecture-diagrams generate --project <project>` to verify
