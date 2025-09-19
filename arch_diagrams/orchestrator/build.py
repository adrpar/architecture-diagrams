from __future__ import annotations
from pathlib import Path
import sys
import tomllib
from typing import Iterable, Optional

from arch_diagrams.adapter.pystructurizr_export import dump_dsl
from arch_diagrams.orchestrator.compose import compose
from arch_diagrams.orchestrator.loader import discover_model_builders, discover_view_specs
from arch_diagrams.orchestrator.select import select_views


def build_workspace_dsl(
    *,
    workspace_name: str = "banking",
    project: Optional[str] = None,
    models_root: Optional[Path] = None,
    views_root: Optional[Path] = None,  # currently unused; discovery uses workspace root
    select_names: Optional[Iterable[str]] = None,
    select_tags: Optional[Iterable[str]] = None,
    select_modules: Optional[Iterable[str]] = None,
    prune_to_views: bool = False,
) -> str:
    root = Path(__file__).resolve().parents[2]
    # Ensure workspace root is importable so 'projects.<project>.*' modules can be imported
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    # Optional project manifest: root-level projects/<project>/project.toml only
    if project:
        manifest_paths = [root / "projects" / project / "project.toml"]
        for manifest in manifest_paths:
            if manifest.exists():
                try:
                    data = tomllib.loads(manifest.read_text())
                    ws_name = data.get("workspace_name") or data.get("name")
                    if ws_name:
                        workspace_name = str(ws_name)
                        break
                except Exception:
                    pass
    builders = discover_model_builders(root, project=project)
    model = compose(builders, name=workspace_name)

    all_specs = discover_view_specs(root, project=project)
    selected = select_views(
        all_specs,
        names=set(select_names or []),
        tags=set(select_tags or []),
        modules=set(select_modules or []),
    )
    for spec in selected:
        spec.build(model)

    if prune_to_views and selected:
        _prune_model_to_views(model)

    return dump_dsl(model)


def _prune_model_to_views(model) -> None:
    """Remove elements not referenced by the selected views.

    Keeps:
      - All Persons/Systems/Containers/Components explicitly included by views (after subject normalization rules)
      - Required parents for view subjects (e.g., subject system or container parents)
      - Relationship endpoints between kept elements
    """
    # Local imports avoided; operate on duck-typed model

    # Collect ids included by views and the view subjects
    keep_ids: set[str] = set()
    subject_ids: set[str] = set()
    for v in model.views:
        # Subject
        subj = getattr(v, 'software_system', None) or getattr(v, 'container', None)
        if subj is not None and hasattr(subj, 'id'):
            subject_ids.add(subj.id)
        # Includes
        for eid in getattr(v, 'include', set()):
            keep_ids.add(eid)
        # Elements referenced by name-based filters (from/to/but-include)
        name_filters = getattr(v, '_name_relationship_filters', [])
        if name_filters:
            def _norm(s: Optional[str]) -> Optional[str]:
                if s is None:
                    return None
                return s.strip().lower().replace('_', '-').replace(' ', '-')

            def _resolve_name_to_id(name: str | None) -> Optional[str]:
                if not name or name == '*':
                    return None
                # Support System/Container
                if '/' in name:
                    sys_name, inner = name.split('/', 1)
                    # Find system by display name
                    sys = next((s for s in model.software_systems.values() if _norm(getattr(s, 'name', None)) == _norm(sys_name)), None)
                    if sys is None:
                        return None
                    cont = next((c for c in getattr(sys, 'containers', []) if _norm(getattr(c, 'name', None)) == _norm(inner)), None)
                    return getattr(cont, 'id', None)
                # Try person by name
                person = next((p for p in model.people.values() if _norm(getattr(p, 'name', None)) == _norm(name)), None)
                if person is not None:
                    return getattr(person, 'id', None)
                # Try software system by name
                sys = next((s for s in model.software_systems.values() if _norm(getattr(s, 'name', None)) == _norm(name)), None)
                if sys is not None:
                    return getattr(sys, 'id', None)
                return None

            for nf in name_filters:
                from_id = _resolve_name_to_id(getattr(nf, 'from_name', None))
                to_id = _resolve_name_to_id(getattr(nf, 'to_name', None))
                if from_id:
                    keep_ids.add(from_id)
                if to_id:
                    keep_ids.add(to_id)
                for bi in getattr(nf, 'but_include_names', ()):
                    bi_id = _resolve_name_to_id(bi)
                    if bi_id:
                        keep_ids.add(bi_id)
    keep_ids |= subject_ids

    # Also keep parents needed for correctness
    def add_parents(e):
        p = getattr(e, 'parent', None)
        while p is not None and hasattr(p, 'id'):
            keep_ids.add(p.id)
            p = getattr(p, 'parent', None)

    for e in list(model.iter_elements()):
        if hasattr(e, 'id') and e.id in keep_ids:
            add_parents(e)

    # Prune software systems and nested containers/components
    systems_to_remove = []
    for sid, system in list(model.software_systems.items()):
        if system.id not in keep_ids:
            # Keep system if any nested container/component is kept
            nested_kept = any(c.id in keep_ids or any(comp.id in keep_ids for comp in c.components) for c in system.containers)
            if not nested_kept and sid not in keep_ids:
                systems_to_remove.append(sid)
        else:
            # Prune containers
            new_containers = []
            for c in system.containers:
                if c.id in keep_ids or any(comp.id in keep_ids for comp in c.components):
                    new_containers.append(c)
            system._containers.clear()
            for c in new_containers:
                system._containers[c.name] = c
    for sid in systems_to_remove:
        model.software_systems.pop(sid, None)

    # Prune people and relationships
    model.people = {pid: p for pid, p in model.people.items() if p.id in keep_ids}
    model.relationships = [r for r in model.relationships if hasattr(r.source, 'id') and hasattr(r.destination, 'id') and r.source.id in keep_ids and r.destination.id in keep_ids]
