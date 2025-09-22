from __future__ import annotations
from pathlib import Path
import sys
import tomllib
from typing import Iterable, Optional

from architecture_diagrams.adapter.pystructurizr_export import dump_dsl
from architecture_diagrams.orchestrator.compose import compose
from architecture_diagrams.orchestrator.loader import discover_model_builders, discover_view_specs, discover_overlays
from architecture_diagrams.orchestrator.select import select_views
from architecture_diagrams.orchestrator.specs import ViewSpec


def build_workspace_dsl(
    *,
    workspace_name: str = "banking",
    project: Optional[str] = None,
    project_path: Optional[Path] = None,
    models_root: Optional[Path] = None,
    views_root: Optional[Path] = None,  # currently unused; discovery uses workspace root
    select_names: Optional[Iterable[str]] = None,
    select_tags: Optional[Iterable[str]] = None,
    select_modules: Optional[Iterable[str]] = None,
    prune_to_views: bool = False,
) -> str:
    root = Path(__file__).resolve().parents[2]
    external_root: Optional[Path] = None
    extra_model_dirs: list[Path] = []
    extra_view_dirs: list[Path] = []
    if project_path is not None:
        pp = Path(project_path).resolve()
        # Determine model/view directories to search
        if (pp / "models").exists() or (pp / "views").exists():
            # Direct project folder
            external_root = pp
            if (pp / "models").exists():
                extra_model_dirs.append(pp / "models")
            if (pp / "views").exists():
                extra_view_dirs.append(pp / "views")
        else:
            # project_path may be a 'projects' root or a parent folder containing a 'projects' dir
            proj_root = pp if pp.name == "projects" else (pp / "projects")
            if project and (proj_root / project / "models").exists():
                external_root = proj_root / project
                extra_model_dirs.append(external_root / "models")
                if (external_root / "views").exists():
                    extra_view_dirs.append(external_root / "views")
            elif project and (proj_root / project / "views").exists():
                external_root = proj_root / project
                if (external_root / "models").exists():
                    extra_model_dirs.append(external_root / "models")
                extra_view_dirs.append(external_root / "views")
            else:
                # Aggregate across all projects under proj_root if present
                if proj_root.exists() and proj_root.is_dir():
                    for sub in proj_root.iterdir():
                        if not sub.is_dir():
                            continue
                        md = sub / "models"
                        vd = sub / "views"
                        if md.exists():
                            extra_model_dirs.append(md)
                        if vd.exists():
                            extra_view_dirs.append(vd)
                # No clear external_root (mixed aggregate)
                external_root = None
        # Ensure Python can import 'projects' as a top-level package for absolute imports in external files
        if external_root is not None:
            # If this is .../projects/<name>, add parent of 'projects'
            if external_root.parent.name == "projects":
                top = external_root.parent.parent
            else:
                # For direct project path, try its parent parent if parent is 'projects'
                top = external_root.parent
                if top.name == "projects":
                    top = top.parent
            if str(top) not in sys.path:
                sys.path.insert(0, str(top))
        else:
            # Aggregate mode: if pp is 'projects', add its parent; if pp contains 'projects', add pp
            top = pp.parent if pp.name == "projects" else pp
            if str(top) not in sys.path:
                sys.path.insert(0, str(top))
    # Ensure workspace root is importable so 'projects.<project>.*' modules can be imported
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    # Optional project manifest: root-level projects/<project>/project.toml only
    if project and external_root is None:
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
    # For external paths, prefer external manifest if present
    if external_root is not None:
        ext_manifest = external_root / "project.toml"
        if ext_manifest.exists():
            try:
                data = tomllib.loads(ext_manifest.read_text())
                ws_name = data.get("workspace_name") or data.get("name")
                if ws_name:
                    workspace_name = str(ws_name)
            except Exception:
                pass

    # Discover from internal repo layout or external project path(s)
    # Resolve inheritance (extends) if present in manifest when using internal project
    base_project: Optional[str] = None
    if project and external_root is None:
        manifest = root / "projects" / project / "project.toml"
        if manifest.exists():
            try:
                data = tomllib.loads(manifest.read_text())
                base_project = data.get("extends")  # type: ignore[assignment]
            except Exception:
                base_project = None

    # Compose base
    if base_project:
        base_builders = discover_model_builders(root, project=base_project)
        model = compose(base_builders, name=workspace_name)
        # Then apply derived project's own builders on top (if any)
        derived_builders = discover_model_builders(root, project=project)
        for b in derived_builders:
            model = b(model)
    else:
        if extra_model_dirs:
            builders = discover_model_builders(root, extra_dirs=extra_model_dirs)
        else:
            builders = discover_model_builders(root, project=project)
        model = compose(builders, name=workspace_name)

    # Apply overlays if any (internal or external)
    overlay_dirs = extra_model_dirs if extra_model_dirs else None
    overlays = discover_overlays(root, project=project, extra_dirs=overlay_dirs)
    for apply in overlays:
        try:
            apply(model)
        except Exception:
            # Best-effort: do not fail the whole build if an overlay raises
            pass

    if extra_view_dirs:
        base_specs = discover_view_specs(root, extra_dirs=extra_view_dirs)
    else:
        base_specs = discover_view_specs(root, project=project)
    # If extends is set, merge base project's views as well (base first to allow perceived override by derived)
    if base_project:
        base_proj_specs = discover_view_specs(root, project=base_project)
        all_specs = _merge_view_inheritance(base_proj_specs, base_specs)
    else:
        all_specs = _merge_view_inheritance([], base_specs)
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


def _merge_view_inheritance(base_specs: list[ViewSpec], derived_specs: list[ViewSpec]) -> list[ViewSpec]:
    """Return a merged list of views where derived views may extend base views by key.

    Rules:
    - If derived view has extends_key matching a base view key:
      - name/view_type default to base if not provided in derived
      - description: derived overrides if set, else base
      - tags: union (base ∪ derived)
      - includes: base + derived (derived appended)
      - excludes: base + derived (derived appended)
      - filters: base + derived
      - subject: derived overrides if set, else base
      - smart: derived overrides if set to True, else keep base
    - Otherwise views are included as-is; base then derived.
    - If multiple base views share same key, first match wins.
    """
    by_key: dict[str, ViewSpec] = {v.key: v for v in base_specs}
    merged: list[ViewSpec] = list(base_specs)
    for dv in derived_specs:
        ek = getattr(dv, 'extends_key', None)
        if not ek:
            merged.append(dv)
            continue
        bv = by_key.get(ek)
        if not bv:
            # No base found; fall back to derived as-is
            merged.append(dv)
            continue
        # Build a new spec by merging fields
        new = ViewSpec(
            key=dv.key or bv.key,
            name=dv.name or bv.name,
            view_type=dv.view_type or bv.view_type,
            description=dv.description or bv.description,
            tags=set(bv.tags) | set(dv.tags),
            includes=list(bv.includes) + list(dv.includes),
            excludes=list(bv.excludes) + list(dv.excludes),
            filters=list(getattr(bv, 'filters', [])) + list(getattr(dv, 'filters', [])),
            subject=dv.subject or bv.subject,
            smart=dv.smart or bv.smart,
        )
        # Override semantics: replace the base view in-place if present; otherwise append
        try:
            idx = merged.index(bv)
        except ValueError:
            idx = -1
        if idx >= 0:
            merged[idx] = new
        else:
            merged.append(new)
    return merged


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
