from __future__ import annotations

import re
from pathlib import Path

from architecture_diagrams.adapter.pystructurizr_export import (  # type: ignore[assignment]
    dump_dsl,
    to_pystructurizr,
)
from architecture_diagrams.orchestrator.build import build_workspace_dsl
from architecture_diagrams.orchestrator.compose import compose
from architecture_diagrams.orchestrator.loader import discover_model_builders, discover_view_specs
from architecture_diagrams.orchestrator.select import select_views


def _extract_view_titles(dsl: str) -> set[str]:
    """Parse pystructurizr DSL and return the set of view titles found in the views block.

    We capture titles for: systemLandscape, systemContext, container, component views.
    Title is the first quoted string after the view kind.
    """
    titles: set[str] = set()
    in_views = False
    depth = 0
    for line in dsl.splitlines():
        s = line.strip()
        if s.startswith("views ") or s == "views {":
            in_views = True
            depth = s.count("{")
            continue
        if in_views:
            depth += s.count("{")
            depth -= s.count("}")
            if depth <= 0:
                in_views = False
                continue
            # Match: systemContext "Title" ... OR container "Title" ... etc
            m = re.match(r"(systemLandscape|systemContext|container|component)\s+\"([^\"]+)\"", s)
            if m:
                titles.add(m.group(2))
    return titles


def test_view_title_parity_default():
    # Build legacy-like DSL via orchestrator
    root = Path(__file__).resolve().parents[1]
    builders = discover_model_builders(root, project="banking")
    model = compose(builders, name="banking")
    specs = discover_view_specs(root, project="banking")
    sel = select_views(specs, names=set(), tags={"default"}, modules=set())
    for s in sel:
        s.build(model)
    legacy_dsl = dump_dsl(to_pystructurizr(model))
    legacy_titles = _extract_view_titles(legacy_dsl)
    # The legacy builder may include a global systemLandscape; in banking we use manifest name.
    legacy_titles.discard("Banking")

    # Orchestrator-generated DSL for tag 'default'
    orch_dsl = build_workspace_dsl(
        select_tags=["default"], project="banking", workspace_name="banking"
    )
    orch_titles = _extract_view_titles(orch_dsl)

    assert orch_titles == legacy_titles


def test_view_title_parity_td():
    # Build legacy-like DSL via orchestrator
    root = Path(__file__).resolve().parents[1]
    builders = discover_model_builders(root, project="banking")
    model = compose(builders, name="banking")
    specs = discover_view_specs(root, project="banking")
    sel = select_views(specs, names=set(), tags={"td"}, modules=set())
    for s in sel:
        s.build(model)
    legacy_dsl = dump_dsl(to_pystructurizr(model))
    legacy_titles = _extract_view_titles(legacy_dsl)
    legacy_titles.discard("Banking")

    # Orchestrator-generated DSL for tag 'td'
    orch_dsl = build_workspace_dsl(select_tags=["td"], project="banking", workspace_name="banking")
    orch_titles = _extract_view_titles(orch_dsl)

    assert orch_titles == legacy_titles
