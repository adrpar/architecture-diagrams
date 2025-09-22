from __future__ import annotations

import re
from typing import Iterable

from architecture_diagrams.adapter.pystructurizr_export import dump_dsl, to_pystructurizr  # type: ignore[assignment]
from architecture_diagrams.orchestrator.build import build_workspace_dsl
from architecture_diagrams.orchestrator.loader import discover_model_builders, discover_view_specs
from architecture_diagrams.orchestrator.compose import compose
from architecture_diagrams.orchestrator.select import select_views
from pathlib import Path


def _extract_first_view_block(dsl: str, title: str) -> str:
    """Extract the first view block for a given title from a pystructurizr DSL string."""
    lines = []
    capture = False
    depth = 0
    for line in dsl.splitlines():
        s = line.strip()
        # start when the view line for this title appears
        if not capture:
            m = re.match(r'(systemLandscape|systemContext|container|component)\s+"([^\"]+)"', s)
            if m and m.group(2) == title:
                capture = True
                depth += s.count('{')
                lines.append(line)
                continue
        else:
            depth += s.count('{')
            depth -= s.count('}')
            lines.append(line)
            if depth <= 0:
                break
    return '\n'.join(lines)


def _normalize(block: str) -> str:
    # Drop whitespace-only lines and normalize spacing
    return '\n'.join(line.rstrip() for line in block.splitlines() if line.strip())


def _titles_for(names: Iterable[str]) -> list[str]:
    # Our ViewSpecs use name as title matching legacy
    return list(names)


# Representative sample: switch to banking. Pick several defined views.
SAMPLE_DEFAULT_TITLES = _titles_for([
    "Banking systems overview",
    "Channels Access XRef",
    "Banking Data Flows",
])


def test_sample_view_block_parity_default():
    # Build a pystructurizr Workspace via orchestrator (legacy-like path)
    root = Path(__file__).resolve().parents[1]
    builders = discover_model_builders(root, project="banking")
    model = compose(builders, name="banking")
    specs = discover_view_specs(root, project="banking")
    sel = select_views(specs, names=set(), tags={"default"}, modules=set())
    for s in sel:
        s.build(model)
    legacy_dsl = dump_dsl(to_pystructurizr(model))
    orch_dsl = build_workspace_dsl(select_tags=["default"], project="banking", workspace_name="banking") 
    for title in SAMPLE_DEFAULT_TITLES:
        legacy_block = _extract_first_view_block(legacy_dsl, title)
        current_block = _extract_first_view_block(orch_dsl, title)
        assert _normalize(current_block) == _normalize(legacy_block), f"Mismatch in view block for {title}"
