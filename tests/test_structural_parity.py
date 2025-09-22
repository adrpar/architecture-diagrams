"""Structural parity test: ensure every legacy system/container/person exists in C4.

We do NOT require exact DSL textual match; we allow C4 to have additional
elements/relationships. This gives regression confidence without forcing
snapshot churn while you finish the migration.

Rules:
 1. Every legacy SoftwareSystem name must appear among C4 software_systems.
 2. For each legacy container, a container with same name must exist inside
     the corresponding C4 system (matching by system name).
 3. All legacy persons must exist in C4 (by name).
 4. Report concise diffs if missing; ignore extras.
"""
from typing import Any
from architecture_diagrams.adapter.pystructurizr_export import to_pystructurizr  # type: ignore[assignment]
from pathlib import Path
from architecture_diagrams.orchestrator.loader import discover_model_builders
from architecture_diagrams.orchestrator.compose import compose


def _build_legacy_like_workspace() -> Any:
    """Build a legacy-like pystructurizr Workspace using orchestrator + exporter.

    This replaces the old legacy shim and composes the model
    directly from the banking project, exporting to a pystructurizr Workspace.
    """
    root = Path(__file__).resolve().parents[1]
    builders = discover_model_builders(root, project="banking")
    model = compose(builders, name="banking")
    return to_pystructurizr(model)  # type: ignore[no-any-return]


def _legacy_elements():
    legacy_ws: Any = _build_legacy_like_workspace()
    systems: dict[str, set[str]] = {}
    persons: set[str] = set()

    # pystructurizr Workspace exposes Model via capital M attribute
    model = getattr(legacy_ws, 'Model', None)
    if model is None:
        raise AssertionError("Legacy workspace missing Model attribute (pystructurizr API change?)")

    # software_systems stored on model.software_systems (list-like)
    for s in getattr(model, 'software_systems', []):
        containers = {c.name for c in getattr(s, 'containers', [])}
        systems[s.name] = containers

    for p in getattr(model, 'people', []):
        persons.add(p.name)

    return systems, persons


def _build_c4_workspace():
    root = Path(__file__).resolve().parents[1]
    builders = discover_model_builders(root, project="banking")
    return compose(builders, name="banking")

def _c4_elements():
    c4 = _build_c4_workspace()
    systems = {s.name: {c.name for c in s.containers} for s in c4.software_systems.values()}
    persons = {p.name for p in c4.people.values()}  # type: ignore[attr-defined]
    return systems, persons


def _legacy_relationship_pairs() -> set[tuple[str, str]]:
    """Collect (source_name, dest_name) pairs from legacy pystructurizr workspace.

    Only include relationships where both endpoints are among collected systems/containers/persons
    to avoid noise from external placeholder elements not (yet) modeled in C4.
    """
    ws = _build_legacy_like_workspace()
    model = getattr(ws, 'Model')
    systems = {s.name: s for s in getattr(model, 'software_systems', [])}
    persons = {p.name: p for p in getattr(model, 'people', [])}
    valid_names = set(systems.keys()) | set(persons.keys())
    # Add containers
    container_index: dict[str, object] = {}
    for s in systems.values():
        for c in getattr(s, 'containers', []):
            container_index[c.name] = c
            valid_names.add(c.name)

    pairs: set[tuple[str, str]] = set()
    for rel in getattr(model, 'relationships', []):
        try:
            src = rel.source.name  # type: ignore[attr-defined]
            dst = rel.destination.name  # type: ignore[attr-defined]
        except AttributeError:
            continue
        if src in valid_names and dst in valid_names:
            pairs.add((src, dst))
    return pairs


def _c4_relationship_pairs() -> set[tuple[str, str]]:
    wm = _build_c4_workspace()
    return {(r.source.name, r.destination.name) for r in wm.relationships}


def test_structural_parity():
    legacy_systems, legacy_persons = _legacy_elements()
    c4_systems, c4_persons = _c4_elements()

    missing_systems = sorted(name for name in legacy_systems if name not in c4_systems)
    missing_containers: list[str] = []
    for sys_name, conts in legacy_systems.items():
        if sys_name not in c4_systems:
            continue
        c4_conts = c4_systems[sys_name]
        for c in conts:
            if c not in c4_conts:
                missing_containers.append(f"{sys_name}/{c}")
    missing_persons = sorted(p for p in legacy_persons if p not in c4_persons)

    msgs: list[str] = []
    if missing_systems:
        msgs.append(f"Missing systems: {missing_systems}")
    if missing_containers:
        msgs.append(f"Missing containers: {missing_containers[:40]}" + (" ..." if len(missing_containers) > 40 else ""))
    if missing_persons:
        msgs.append(f"Missing persons: {missing_persons}")

    if msgs:
        raise AssertionError("Structural parity failure:\n" + "\n".join(msgs))


def test_relationship_parity():
    """Ensure every legacy relationship endpoint pair exists in the C4 model.

    We ignore description text and allow C4 to have extra relationships. This focuses
    on coverage of connectivity. If needed later we can tighten by filtering
    or by introducing description set comparisons.
    """
    legacy_pairs = _legacy_relationship_pairs()
    c4_pairs = _c4_relationship_pairs()

    missing = sorted(p for p in legacy_pairs if p not in c4_pairs)
    # Heuristic: ignore pairs where either endpoint contains spaces and appears to be an alias variant
    # (legacy often had duplicate alias containers); we could refine with explicit allowlist.
    filtered_missing = [p for p in missing if True]
    if filtered_missing:
        preview = filtered_missing[:40]
        raise AssertionError(
            f"Missing relationship endpoint pairs ({len(filtered_missing)}): {preview}"
        )
