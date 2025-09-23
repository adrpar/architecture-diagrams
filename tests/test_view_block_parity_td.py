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


def _extract_first_view_block(dsl: str, title: str) -> str:
    lines: list[str] = []
    capture = False
    depth = 0
    for line in dsl.splitlines():
        s = line.strip()
        if not capture:
            m = re.match(r"(systemLandscape|systemContext|container|component)\s+\"([^\"]+)\"", s)
            if m and m.group(2) == title:
                capture = True
                depth += s.count("{")
                lines.append(line)
                continue
        else:
            depth += s.count("{")
            depth -= s.count("}")
            lines.append(line)
            if depth <= 0:
                break
    return "\n".join(lines)


def _normalize(block: str) -> str:
    return "\n".join(line.rstrip() for line in block.splitlines() if line.strip())


SAMPLE_TD_TITLES = [
    "Clearing XRef",
    "Eventing-focused XRef",
    "Open Banking minimal XRef",
]


def test_sample_view_block_parity_td():
    # Build a pystructurizr Workspace via orchestrator (legacy-like path)
    root = Path(__file__).resolve().parents[1]
    builders = discover_model_builders(root, project="banking")
    model = compose(builders, name="banking")
    specs = discover_view_specs(root, project="banking")
    sel = select_views(specs, names=set(), tags={"td"}, modules=set())
    for s in sel:
        s.build(model)
    legacy_dsl = dump_dsl(to_pystructurizr(model))
    orch_dsl = build_workspace_dsl(select_tags=["td"], project="banking", workspace_name="banking")
    for title in SAMPLE_TD_TITLES:
        legacy_block = _extract_first_view_block(legacy_dsl, title)
        current_block = _extract_first_view_block(orch_dsl, title)
        assert _normalize(current_block) == _normalize(
            legacy_block
        ), f"Mismatch in view block for {title}"
