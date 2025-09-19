# Projects layout and usage

This repository supports multiple projects under the repository root `projects/<project>` only. Each project has independent models and views.

- Models: `projects/<project>/models` — modules `*_c4.py` must export `define_<name>(model)` and optionally `link_<name>(model)`
- Views: `projects/<project>/views` — modules export `get_views()` which returns a list of `ViewSpec`
- Optional manifest: `projects/<project>/project.toml` — allows overriding the workspace name. Example:

```
workspace_name = "Banking"
```

## CLI

Always use uv.

- Generate DSL for a project:

```
uv run arch-diags generate --project banking --output workspace.dsl
```

- List views for a project:

```
uv run arch-diags list-views --project banking
```

- List modules inferred from views (subjects):

```
uv run arch-diags list-modules --project banking
```

- Selective generation by names, tags, or modules:

```
uv run arch-diags generate --project banking --views ReportingDataLineage,BankingDataFlows
uv run arch-diags generate --project banking --tags analytics,channels
uv run arch-diags generate --project banking --modules payments,channels
```

## Name-based relationship filters

Views can add filters that generate `include A->B` or `exclude A->B` lines in the DSL by referring to elements by display names, including nested forms like `System/Container`.
Use `IncludeRelByName` and `ExcludeRelByName` in `arch_diagrams.orchestrator.specs`.

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
- Run: `uv run arch-diags generate --project <project>` to verify
