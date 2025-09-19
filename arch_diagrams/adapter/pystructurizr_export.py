"""Adapter that converts internal C4 model to pystructurizr Workspace.

This exporter now always generates fresh DSL from the internal model. Any
previous baseline/parity mode has been removed to simplify behavior and
avoid snapshot coupling.
"""
from __future__ import annotations
from typing import Dict, Optional, Iterable
from pystructurizr.dsl import Workspace, Person as DPerson, SoftwareSystem as DSoftwareSystem, Dumper, View as DView

from arch_diagrams.c4 import (
    SystemLandscapeView,
    SmartSystemLandscapeView,
    SystemContextView,
    ContainerView,
    ComponentView,
    SystemLandscape,
)
from arch_diagrams.extensions.smart_views import SmartView

# NOTE: Deployment and infrastructure mapping left for future extension since not used yet.

def to_pystructurizr(model: SystemLandscape) -> Workspace:
    ws = Workspace()
    dsl_model = ws.Model(name=model.name)

    element_mapping: Dict[str, object] = {}
    # De-duplication registries by display name (and hierarchy for nested types)
    seen_persons: Dict[str, DPerson] = {}
    seen_systems: Dict[str, DSoftwareSystem] = {}
    seen_containers: Dict[tuple[str, str], object] = {}
    seen_components: Dict[tuple[str, str, str], object] = {}

    # People
    id_to_model: Dict[str, object] = {}
    for person in model.people.values():
        existing = seen_persons.get(person.name)
        if existing is None:
            p = DPerson(person.name, person.description)
            seen_persons[person.name] = p
            dsl_model.Person(p)
        else:
            p = existing
        element_mapping[person.id] = p
        id_to_model[person.id] = person

    # Software Systems & nested
    for system in model.software_systems.values():
        ss = seen_systems.get(system.name)
        if ss is None:
            ss = DSoftwareSystem(system.name, system.description)
            seen_systems[system.name] = ss
            dsl_model.SoftwareSystem(ss)
        element_mapping[system.id] = ss
        id_to_model[system.id] = system
        # Containers
        for container in system.containers:
            c_key = (system.name, container.name)
            dc = seen_containers.get(c_key)
            if dc is None:
                dc = ss.Container(container.name, container.description, container.technology or "")
                seen_containers[c_key] = dc
            element_mapping[container.id] = dc
            id_to_model[container.id] = container
            # Components
            for component in container.components:
                comp_key = (system.name, container.name, component.name)
                comp = seen_components.get(comp_key)
                if comp is None:
                    comp = dc.Component(component.name, component.description, component.technology or "")
                    seen_components[comp_key] = comp
                element_mapping[component.id] = comp
                id_to_model[component.id] = component

    # Relationships (respect any relationship restrictions)
    sys_level_edges: set[tuple[str, str]] = set()
    for rel in model.get_effective_relationships():  # type: ignore[attr-defined]
        src = element_mapping.get(rel.source.id)
        dst = element_mapping.get(rel.destination.id)
        if src and dst and hasattr(src, "uses"):
            src.uses(dst, rel.description, rel.technology or "")  # type: ignore[arg-type]
        # Build aggregated system-level relationships for system landscape views
        try:
            src_model = id_to_model.get(rel.source.id)
            dst_model = id_to_model.get(rel.destination.id)
            # Walk up to parent systems
            def _parent_system(mobj: object) -> Optional[object]:
                cur = mobj
                for _ in range(4):
                    parent = getattr(cur, 'parent', None)
                    if parent is None:
                        return None
                    from arch_diagrams.c4.model import SoftwareSystem as _MS
                    if isinstance(parent, _MS):
                        return parent
                    cur = parent
                return None
            ps = _parent_system(src_model) if src_model is not None else None
            pd = _parent_system(dst_model) if dst_model is not None else None
            if ps is not None and pd is not None and getattr(ps, 'id', None) != getattr(pd, 'id', None):
                d_src_sys = element_mapping.get(getattr(ps, 'id', ''))
                d_dst_sys = element_mapping.get(getattr(pd, 'id', ''))
                if d_src_sys is not None and d_dst_sys is not None and hasattr(d_src_sys, 'uses'):
                    key = (getattr(d_src_sys, 'instname', ''), getattr(d_dst_sys, 'instname', ''))
                    if key not in sys_level_edges:
                        # Add a lightweight aggregated relationship
                        d_src_sys.uses(d_dst_sys, "", "")  # type: ignore[arg-type]
                        sys_level_edges.add(key)
        except Exception:
            # Fail-safe: do not block export on aggregation issues
            pass

    # (Legacy smart metadata support removed; smart views must be created explicitly.)

    # Standard (non-smart) views first, preserving declaration order
    for view in [v for v in model.views if not isinstance(v, SmartSystemLandscapeView)]:
        if isinstance(view, SystemLandscapeView):
            dview = ws.SystemLandscapeView(view.name, view.description or view.name)
        elif isinstance(view, SystemContextView):
            # Resolve a SoftwareSystem for the subject (map container/component to parent system)
            subj = _resolve_view_subject(view, id_to_model, element_mapping)
            if subj is None:
                continue
            dview = ws.SystemContextView(subj, view.name, view.description or view.name)  # type: ignore[arg-type]
        elif isinstance(view, ContainerView):
            # Resolve a SoftwareSystem for the subject (map container to parent system if needed)
            subj = _resolve_view_subject(view, id_to_model, element_mapping)
            if subj is None:
                continue
            dview = ws.ContainerView(subj, view.name, view.description or view.name)  # type: ignore[arg-type]
        elif isinstance(view, ComponentView):
            # Resolve a Container for the subject (map component to parent container if needed)
            subj = _resolve_view_subject(view, id_to_model, element_mapping)
            if subj is None:
                continue
            dview = ws.ComponentView(subj, view.name, view.description or view.name)  # type: ignore[arg-type]
        else:
            continue
        for element in _normalized_include_elements(view, id_to_model, element_mapping):  # deterministic
            dview.include(element)  # type: ignore[arg-type]
        # Note: pystructurizr's ws.System*View methods already register the view in ws.views,
        # so do NOT append again to avoid duplicates.

    # Smart system landscape views using SmartView (include * semantics handled by its dump)
    for view in [v for v in model.views if isinstance(v, SmartSystemLandscapeView)]:
        sv = SmartView(DView.Kind.SYSTEM_LANDSCAPE, None, view.name, view.description or view.name)
        # Deterministic ordering: slug sort
        def _slug(obj):
            n = getattr(obj, "name", "")
            return n.lower().replace(" ", "_")
        elements_for_view = []
        for element_id in view.include:
            element = element_mapping.get(element_id)
            if element is not None:
                elements_for_view.append(element)
        for element in sorted(elements_for_view, key=_slug):
            sv.include(element)  # type: ignore[arg-type]
        ws.views.append(sv)

    return ws


def _normalized_include_elements(view: object, id_to_model: Dict[str, object], element_mapping: Dict[str, object]) -> Iterable[object]:
    """Yield DSL elements to include, normalizing per view type rules.

    - SystemContextView: allow Person and SoftwareSystem; map Container/Component to parent SoftwareSystem.
    - ContainerView: allow Person, SoftwareSystem, and Containers within the subject software system; map external Container/Component to parent SoftwareSystem.
    - ComponentView: allow Person, SoftwareSystem, Containers (external), and Components within the subject container; map external Component to its parent Container.
    """
    from arch_diagrams.c4.model import Person as MPerson, SoftwareSystem as MSystem, Container as MContainer, Component as MComponent
    from arch_diagrams.c4.model import SystemContextView as MSystemContextView, ContainerView as MContainerView, ComponentView as MComponentView

    def _parent_system(obj: object) -> Optional[object]:
        # Walk parent pointers until a SoftwareSystem or None
        cur = obj
        for _ in range(3):
            parent = getattr(cur, 'parent', None)
            if parent is None:
                return None
            if isinstance(parent, MSystem):
                return parent
            cur = parent
        return None

    def _parent_container(obj: object) -> Optional[object]:
        cur = obj
        for _ in range(3):
            parent = getattr(cur, 'parent', None)
            if parent is None:
                return None
            if isinstance(parent, MContainer):
                return parent
            cur = parent
        return None

    include_ids = sorted(getattr(view, 'include', set()))

    if isinstance(view, MSystemContextView):
        for eid in include_ids:
            m = id_to_model.get(eid)
            if m is None:
                continue
            if isinstance(m, (MPerson, MSystem)):
                el = element_mapping.get(eid)
                if el is not None:
                    yield el
            elif isinstance(m, (MContainer, MComponent)):
                ps = _parent_system(m)
                if ps is not None:
                    el = element_mapping.get(getattr(ps, 'id'))
                    if el is not None:
                        yield el
        return

    if isinstance(view, MContainerView):
        subj: Optional[object] = getattr(view, 'software_system', None)
        subj_id = getattr(subj, 'id', None)
        for eid in include_ids:
            m = id_to_model.get(eid)
            if m is None:
                continue
            if isinstance(m, MPerson):
                el = element_mapping.get(eid)
                if el is not None:
                    yield el
            elif isinstance(m, MSystem):
                el = element_mapping.get(eid)
                if el is not None:
                    yield el
            elif isinstance(m, MContainer):
                # Only include containers within the subject system; otherwise include the parent system
                ps = _parent_system(m)
                if ps is not None and getattr(ps, 'id', None) == subj_id:
                    el = element_mapping.get(eid)
                    if el is not None:
                        yield el
                else:
                    if ps is not None:
                        el = element_mapping.get(getattr(ps, 'id'))
                        if el is not None:
                            yield el
            elif isinstance(m, MComponent):
                # Components are not directly included in container view; include parent system instead
                ps = _parent_system(m)
                if ps is not None:
                    el = element_mapping.get(getattr(ps, 'id'))
                    if el is not None:
                        yield el
        return

    if isinstance(view, MComponentView):
        subj: Optional[object] = getattr(view, 'container', None)
        subj_id = getattr(subj, 'id', None)
        for eid in include_ids:
            m = id_to_model.get(eid)
            if m is None:
                continue
            if isinstance(m, (MPerson, MSystem)):
                el = element_mapping.get(eid)
                if el is not None:
                    yield el
            elif isinstance(m, MContainer):
                # External containers allowed
                el = element_mapping.get(eid)
                if el is not None:
                    yield el
            elif isinstance(m, MComponent):
                # Only include components within the subject container
                pc = _parent_container(m)
                if pc is not None and getattr(pc, 'id', None) == subj_id:
                    el = element_mapping.get(eid)
                    if el is not None:
                        yield el
        return

    # Default: yield as-is
    for eid in include_ids:
        el = element_mapping.get(eid)
        if el is not None:
            yield el

def _resolve_view_subject(view: object, id_to_model: Dict[str, object], element_mapping: Dict[str, object]) -> Optional[object]:
    """Return the correct subject element for the view header.

    - SystemContextView expects a SoftwareSystem
    - ContainerView expects a SoftwareSystem (subject system)
    - ComponentView expects a Container
    """
    from arch_diagrams.c4.model import Person as MPerson, SoftwareSystem as MSystem, Container as MContainer, Component as MComponent
    from arch_diagrams.c4.model import SystemContextView as MSystemContextView, ContainerView as MContainerView, ComponentView as MComponentView

    def _parent_system(obj: object) -> Optional[object]:
        cur = obj
        for _ in range(4):
            parent = getattr(cur, 'parent', None)
            if parent is None:
                return None
            if isinstance(parent, MSystem):
                return parent
            cur = parent
        return None

    def _parent_container(obj: object) -> Optional[object]:
        cur = obj
        for _ in range(4):
            parent = getattr(cur, 'parent', None)
            if parent is None:
                return None
            if isinstance(parent, MContainer):
                return parent
            cur = parent
        return None

    if isinstance(view, MSystemContextView):
        subj = getattr(view, 'software_system', None)
        if subj is None:
            return None
        m = id_to_model.get(getattr(subj, 'id', '' ))
        if m is None:
            return None
        if isinstance(m, MSystem):
            return element_mapping.get(getattr(subj, 'id', ''))
        if isinstance(m, (MContainer, MComponent)):
            ps = _parent_system(m)
            if ps is None:
                return None
            return element_mapping.get(getattr(ps, 'id', ''))
        return None

    if isinstance(view, MContainerView):
        subj = getattr(view, 'software_system', None)
        if subj is None:
            return None
        m = id_to_model.get(getattr(subj, 'id', '' ))
        if m is None:
            return None
        if isinstance(m, MSystem):
            return element_mapping.get(getattr(subj, 'id', ''))
        if isinstance(m, (MContainer, MComponent)):
            ps = _parent_system(m)
            if ps is None:
                return None
            return element_mapping.get(getattr(ps, 'id', ''))
        return None

    if isinstance(view, MComponentView):
        subj = getattr(view, 'container', None)
        if subj is None:
            return None
        m = id_to_model.get(getattr(subj, 'id', '' ))
        if m is None:
            return None
        if isinstance(m, MContainer):
            return element_mapping.get(getattr(subj, 'id', ''))
        if isinstance(m, MComponent):
            pc = _parent_container(m)
            if pc is None:
                return None
            return element_mapping.get(getattr(pc, 'id', ''))
        return None

    return None


def dump_dsl(model) -> str:  # type: ignore[override]
    """Dump DSL for either new C4 SystemLandscape or legacy pystructurizr Workspace."""
    # Legacy workspace path
    if isinstance(model, Workspace):
        dumper = Dumper()
        return model.dump(dumper=dumper)

    # New C4 model path
    ws = to_pystructurizr(model)
    dumper = Dumper()
    dsl = ws.dump(dumper=dumper)
    dsl = _ensure_group_separator(dsl)
    dsl = _inject_or_augment_styles(dsl, model)
    dsl = _reorder_relationships_after_declarations(dsl)
    # Optionally reduce cosmetic _2/_3 suffixes where safe (no base-name collisions)
    dsl = _canonicalize_variable_suffixes(dsl)
    dsl = _inject_workspace_name_comment(dsl, model)
    # Apply any name-based relationship filters declared in ViewSpecs (explicit over heuristics)
    dsl = _apply_name_filters(dsl, model)
    # Normalize invalid include lines in views after generation (e.g., containers in systemContext)
    # Run after name filters so we can detect sentinel and avoid generic excludes that hide intended relations.
    dsl = _fix_view_includes(dsl)
    return dsl


# --- Refactored helper functions (string based; candidates for future full DSL generator) ---
def _ensure_group_separator(dsl: str) -> str:
    if '"structurizr.groupSeparator"' in dsl:
        return dsl
    lines = dsl.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == 'model {':
            prop_block = [
                '    properties {',
                '      "structurizr.groupSeparator" "/"',
                '    }'
            ]
            lines[i+1:i+1] = prop_block
            return '\n'.join(lines)
    return dsl

    

def _inject_or_augment_styles(dsl: str, model: SystemLandscape) -> str:
    if 'views {' not in dsl:
        return dsl
    element_styles = model.styles.element_styles
    rel_styles = model.styles.relationship_styles
    synthesized = ('styles {' not in dsl) and (not element_styles and not rel_styles)
    lines = dsl.splitlines()
    style_start = None
    style_end = None
    depth = 0
    for i, line in enumerate(lines):
        if 'styles {' in line:
            style_start = i
        if style_start is not None:
            if '{' in line:
                depth += line.count('{')
            if '}' in line:
                depth -= line.count('}')
            if depth == 0 and style_start is not None:
                style_end = i
                break
    insert_index = None
    in_landscape = False
    saw_auto = False
    for i, line in enumerate(lines):
        if line.strip().startswith('systemLandscape'):
            in_landscape = True
        elif in_landscape:
            if 'autoLayout' in line:
                saw_auto = True
            if line.strip() == '}' and saw_auto:
                insert_index = i + 1
                break
    if insert_index is None:
        for i, line in enumerate(lines):
            if line.strip() == 'views {':
                insert_index = i + 1
                break
    if style_start is None and insert_index is not None:
        style_block: list[str] = ['    styles {']
        if synthesized:
            defaults = [
                ('Element', {'shape': 'RoundedBox'}),
                ('Software System', {'background': '#1168bd', 'color': '#ffffff'}),
                ('Container', {'background': '#438dd5', 'color': '#ffffff'}),
                ('Component', {'background': '#85bbf0', 'color': '#000000'}),
                ('Person', {'background': '#08427b', 'color': '#ffffff', 'shape': 'Person'}),
                ('Infrastructure Node', {'background': '#ffffff'}),
                ('database', {'shape': 'Cylinder'}),
                ('Container', {'shape': 'RoundedBox', 'description': 'true'}),
                ('Person', {'shape': 'Person'}),
                ('external', {'background': '#808080'}),
                ('storage', {'shape': 'Cylinder'}),
                ('library', {'shape': 'Folder'}),
            ]
            for tag, attrs in defaults:
                style_block.append(f'      element "{tag}" {{')
                for k, v in attrs.items():
                    style_block.append(f'        {k} "{v}"')
                style_block.append('      }')
        else:
            for es in element_styles:
                style_block.append(f'      element "{es.tag}" {{')
                if es.background:
                    style_block.append(f'        background "{es.background}"')
                if es.color:
                    style_block.append(f'        color "{es.color}"')
                if es.shape:
                    style_block.append(f'        shape "{es.shape}"')
                if es.opacity is not None:
                    style_block.append(f'        opacity "{es.opacity}"')
                style_block.append('      }')
            for rs in rel_styles:
                style_block.append(f'      relationship "{rs.tag}" {{')
                if rs.color:
                    style_block.append(f'        color "{rs.color}"')
                if rs.dashed is not None:
                    style_block.append(f'        dashed "{str(rs.dashed).lower()}"')
                if rs.thickness is not None:
                    style_block.append(f'        thickness "{rs.thickness}"')
                style_block.append('      }')
        style_block.append('    }')
        lines[insert_index:insert_index] = style_block
        return '\n'.join(lines)
    # augment path
    baseline_required = [
        ('Container', {'shape': 'RoundedBox', 'description': 'true'}),
        ('Person', {'shape': 'Person'}),
        ('external', {'background': '#808080'}),
        ('storage', {'shape': 'Cylinder'}),
        ('library', {'shape': 'Folder'}),
    ]
    if style_start is not None and style_end is not None:
        existing_block = '\n'.join(lines[style_start:style_end+1])
        additions: list[str] = []
        for tag, attrs in baseline_required:
            if f'element "{tag}"' not in existing_block:
                additions.append(f'      element "{tag}" {{')
                for k, v in attrs.items():
                    additions.append(f'        {k} "{v}"')
                additions.append('      }')
        if additions:
            lines.insert(style_end, '\n'.join(additions))
    return '\n'.join(lines)

def _inject_workspace_name_comment(dsl: str, model: SystemLandscape) -> str:
    if model.name in dsl:
        return dsl
    lines = dsl.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith('workspace'):
            lines.insert(i + 1, f'  // {model.name}')
            break
    return '\n'.join(lines)

def _reorder_relationships_after_declarations(dsl: str) -> str:
    """Move all relationship lines ("a -> b ...") to the end of the model block.

    Some Structurizr DSL parsers require variables to be declared before they
    are referenced in relationships. Reordering ensures declarations precede uses.
    """
    lines = dsl.splitlines()
    # Find the model { ... } block range
    model_start = None
    model_end = None
    depth = 0
    for i, line in enumerate(lines):
        if line.strip() == 'model {':
            model_start = i
            depth = 1
            for j in range(i + 1, len(lines)):
                depth += lines[j].count('{') - lines[j].count('}')
                if depth == 0:
                    model_end = j
                    break
            break
    if model_start is None or model_end is None:
        return dsl
    # Collect relationship lines and remove them from their positions
    rel_lines: list[str] = []
    kept: list[str] = []
    for idx in range(model_start + 1, model_end):
        line = lines[idx]
        if '->' in line and '"' in line:
            rel_lines.append(line)
        else:
            kept.append(line)
    # Rebuild: model { + kept + rel_lines + closing
    new_lines = []
    new_lines.extend(lines[:model_start + 1])
    new_lines.extend(kept)
    if rel_lines:
        # Ensure a blank separator for readability
        if kept and kept[-1].strip() != '':
            new_lines.append('')
        new_lines.extend(rel_lines)
    new_lines.extend(lines[model_end:])
    return '\n'.join(new_lines)

def _canonicalize_variable_suffixes(dsl: str) -> str:
    """Best-effort cleanup: rename variables like foo_2 -> foo (and all references)
    when safe to do so.

    Safety rules:
    - Only consider renaming when there is exactly ONE declaration sharing the same base name.
      If multiple declarations share a base (e.g., smart_auth_3 and smart_auth_4), skip that base.
    - Never override an existing declared base name.
    """
    import re
    decl_re = re.compile(r'^(\s*)([A-Za-z0-9_]+)\s*=\s*(SoftwareSystem|Container|Component|Person)\s+"([^"\\]+)"', re.MULTILINE)
    # Collect declarations and group by base
    declared: dict[str, str] = {}  # var -> type
    base_groups: dict[str, list[str]] = {}
    for m in decl_re.finditer(dsl):
        var = m.group(2)
        typ = m.group(3)
        declared[var] = typ
        base_m = re.match(r'^(.*)_([0-9]+)$', var)
        base = base_m.group(1) if base_m else var
        base_groups.setdefault(base, []).append(var)

    # Build renames only for bases with a single suffixed declaration and no existing unsuffixed declaration
    renames: dict[str, str] = {}
    for base, vars_for_base in base_groups.items():
        if base in declared:
            continue  # base already declared, skip
        if len(vars_for_base) == 1 and re.match(r'.*_\d+$', vars_for_base[0]):
            renames[vars_for_base[0]] = base

    if not renames:
        return dsl

    # Apply renames with word-boundary safety
    def _replace(match: re.Match[str]) -> str:
        word = match.group(0)
        return renames.get(word, word)

    pattern = re.compile(r'\b(' + '|'.join(re.escape(k) for k in sorted(renames.keys(), key=len, reverse=True)) + r')\b')
    return pattern.sub(_replace, dsl)

def _fix_view_includes(dsl: str) -> str:
    """Post-process the views section to ensure only valid include targets per view type.

    Mapping rules:
    - systemContext: if include is a Container/Component, map to its parent SoftwareSystem
    - container: if include is a Container outside the subject, map to its parent SoftwareSystem;
                 if include is a Component, map to its parent SoftwareSystem
    - component: if include is a Component outside the subject, map to its parent Container
    """
    import re

    # Build an index of declarations: var -> {type, parentSystem, parentContainer}
    model_start = dsl.find('\n  model {')
    views_start = dsl.find('\n  views {')
    if model_start == -1 or views_start == -1:
        return dsl
    model_block = dsl[model_start:views_start]

    decl_re = re.compile(r'^(\s*)([A-Za-z0-9_]+)\s*=\s*(SoftwareSystem|Container|Component|Person)\s+"([^"\\]+)"', re.MULTILINE)
    var_info: dict[str, dict[str, str | None]] = {}
    stack: list[tuple[str, str]] = []  # (var, type)
    # Simple brace-aware scan
    for line in model_block.splitlines():
        m = decl_re.match(line)
        if m:
            var = m.group(2)
            typ = m.group(3)
            disp = m.group(4)
            parent_system = None
            parent_container = None
            # Determine parents from stack
            for pvar, ptyp in reversed(stack):
                if parent_system is None and ptyp == 'SoftwareSystem':
                    parent_system = pvar
                if parent_container is None and ptyp == 'Container':
                    parent_container = pvar
                if parent_system and parent_container:
                    break
            var_info[var] = {
                'type': typ,
                'parentSystem': parent_system,
                'parentContainer': parent_container,
                'displayName': disp,
            }
            # Push current declaration if block opens
            if '{' in line and '}' not in line:
                stack.append((var, typ))
            continue
        # Track braces for exiting blocks
        open_count = line.count('{')
        close_count = line.count('}')
        for _ in range(open_count - close_count):
            # Unknown block opening, keep stack unchanged (handled on declarations)
            pass
        for _ in range(close_count):
            if stack:
                stack.pop()

    # Build relationship index from model block: list of (src, dst)
    rels: list[tuple[str, str]] = []
    import re as _re
    for line in model_block.splitlines():
        # match: src -> dst "..."
        mrel = _re.search(r'^\s*([A-Za-z0-9_]+)\s*->\s*([A-Za-z0-9_]+)\s*"', line)
        if mrel:
            rels.append((mrel.group(1), mrel.group(2)))

    # Process views block and rewrite include targets
    lines = dsl.splitlines()
    out_lines: list[str] = []
    in_views = False
    current_view_type: str | None = None  # 'systemContext' | 'container' | 'component'
    current_subject: str | None = None
    includes_seen_in_view: set[str] = set()

    view_header_re = re.compile(r'^\s*(systemContext|container|component)\s+([A-Za-z0-9_]+)\s*\{')
    # systemLandscape views (no subject)
    landscape_header_re = re.compile(r'^\s*(systemLandscape)\s*\{')
    # Match include lines, supporting wildcard '*' as well as variable names
    include_re = re.compile(r'^(\s*)include\s+(\*|[A-Za-z0-9_]+)\s*$')
    # Relationship filters may be stashed as sentinel comments; detect generic excludes
    # rf_exclude_re intentionally unused; left as reference for potential future parsing

    injected_exclude_in_view = False
    injected_name_filters_in_view = False
    saw_wildcard_include_in_view = False
    for line in lines:
        if line.strip() == 'views {':
            in_views = True
            out_lines.append(line)
            continue
        if not in_views:
            injected_exclude_in_view = False
            out_lines.append(line)
            continue

        # Detect view header
        mhead = view_header_re.match(line)
        if mhead:
            current_view_type = mhead.group(1)
            current_subject = mhead.group(2)
            # Normalize header subject to correct element type
            subj = current_subject
            s_info = var_info.get(subj or '')
            if s_info:
                stype = s_info['type']  # type: ignore[assignment]
                ps = s_info.get('parentSystem')  # type: ignore[assignment]
                pc = s_info.get('parentContainer')  # type: ignore[assignment]
                if current_view_type in ('systemContext', 'container'):
                    # Expect a SoftwareSystem
                    if stype in ('Container', 'Component') and ps:
                        subj = str(ps)
                elif current_view_type == 'component':
                    # Expect a Container
                    if stype == 'Component' and pc:
                        subj = str(pc)
            includes_seen_in_view = set()
            saw_wildcard_include_in_view = False
            # Rebuild the header with possibly updated subject
            leading_ws = line[: line.find(mhead.group(1))]
            out_lines.append(f"{leading_ws}{current_view_type} {subj} {{")
            # Update current_subject to normalized value for include checks
            current_subject = subj
            continue

        # Detect systemLandscape header (no subject)
        mland = landscape_header_re.match(line)
        if mland:
            current_view_type = mland.group(1)
            current_subject = None
            includes_seen_in_view = set()
            saw_wildcard_include_in_view = False
            out_lines.append(line)
            continue

        # Before closing a view, inject relationship filters (non-landscape only)
        if in_views and line.strip() == '}':
            if current_view_type is not None:
                # For systemLandscape: do nothing here (no blanket excludes or manual rel includes)
                # For other views without wildcard and no name filters: curate edges to avoid noise
                if current_view_type != 'systemLandscape':
                    if not saw_wildcard_include_in_view and not injected_name_filters_in_view:
                        if not injected_exclude_in_view:
                            out_lines.append('      exclude *->*')
                        allowed = sorted(
                            [(s, d) for (s, d) in rels if s in includes_seen_in_view and d in includes_seen_in_view],
                            key=lambda t: (t[0], t[1])
                        )
                        for s, d in allowed:
                            out_lines.append(f'      include {s}->{d}')
            current_view_type = None
            current_subject = None
            includes_seen_in_view = set()
            injected_exclude_in_view = False
            injected_name_filters_in_view = False
            saw_wildcard_include_in_view = False
            out_lines.append(line)
            continue

        # For landscape views, don't inject blanket excludes; let Structurizr render system-level relationships.
        if current_view_type == 'systemLandscape' and 'autoLayout' in line:
            lookback = out_lines[-5:]
            if any('//__NAME_FILTERS__' in lb for lb in lookback):
                injected_name_filters_in_view = True
            out_lines.append(line)
            continue

        # Rewrite include lines
        minc = include_re.match(line)
        if minc and current_view_type is not None:
            indent, var = minc.group(1), minc.group(2)
            if var == '*':
                out_lines.append(line)
                saw_wildcard_include_in_view = True
                continue
            info = var_info.get(var)
            new_var = var
            if info:
                vtype = info['type']  # type: ignore[assignment]
                parent_sys = info['parentSystem']  # type: ignore[assignment]
                parent_cont = info['parentContainer']  # type: ignore[assignment]
                if current_view_type == 'systemContext':
                    if vtype in ('Container', 'Component') and parent_sys:
                        new_var = parent_sys
                elif current_view_type == 'container':
                    if vtype == 'Component' and parent_sys:
                        new_var = parent_sys
                    elif vtype == 'Container':
                        # Keep if same subject system, else map to parent system
                        subj_info = var_info.get(current_subject or '')
                        subj_sys = current_subject if (subj_info and subj_info.get('type') == 'SoftwareSystem') else (subj_info.get('parentSystem') if subj_info else None)
                        if parent_sys and subj_sys and parent_sys != subj_sys:
                            new_var = parent_sys
                elif current_view_type == 'component':
                    if vtype == 'Component' and parent_cont and (current_subject and parent_cont != current_subject):
                        new_var = parent_cont
            # Deduplicate includes within the same view
            if new_var in includes_seen_in_view:
                continue
            includes_seen_in_view.add(new_var)
            out_lines.append(f'{indent}include {new_var}')
            continue

        # For non-landscape views, before autoLayout, ensure wildcard include
        if current_view_type in ('systemContext', 'container', 'component') and 'autoLayout' in line:
            if not saw_wildcard_include_in_view:
                out_lines.append('      include *')
                saw_wildcard_include_in_view = True
            # If earlier pass injected name-based filters, mark flag to suppress generic excludes
            # Detection: look back a few lines for sentinel
            lookback = out_lines[-5:]
            if any('//__NAME_FILTERS__' in lb for lb in lookback):
                injected_name_filters_in_view = True
            out_lines.append(line)
            continue

        out_lines.append(line)

    return '\n'.join(out_lines)


def _apply_name_filters(dsl: str, model: SystemLandscape) -> str:
    """Inject NameRelationshipFilter lines into the appropriate views.

    If a view declares any NameRelationshipFilter, we will add the corresponding exclude/include
    lines just before autoLayout within that view, and suppress generic exclude/include generation
    in _fix_view_includes by setting a sentinel flag comment.
    """
    # Fast path: if no such filters were declared anywhere, skip
    from arch_diagrams.orchestrator.specs import IncludeRelByName, ExcludeRelByName  # local import to avoid cycles during tooling
    # Build view lists for filter detection
    all_views = list(getattr(model, 'views', []))
    non_smart_views = [v for v in all_views if not isinstance(v, SmartSystemLandscapeView)]
    smart_landscapes = [v for v in all_views if isinstance(v, SmartSystemLandscapeView)]
    has_filters_any = (
        any(getattr(v, '_name_relationship_filters', None) for v in non_smart_views) or
        any(getattr(v, '_element_excludes_names', None) for v in non_smart_views) or
        any(getattr(v, '_name_relationship_filters', None) for v in smart_landscapes) or
        any(getattr(v, '_element_excludes_names', None) for v in smart_landscapes)
    )
    if not has_filters_any:
        return dsl

    # Build declaration index: var -> {displayName, type, parentSystem, parentContainer}
    import re
    model_start = dsl.find('\n  model {')
    views_start = dsl.find('\n  views {')
    if model_start == -1 or views_start == -1:
        return dsl
    model_block = dsl[model_start:views_start]
    decl_re = re.compile(r'^(\s*)([A-Za-z0-9_]+)\s*=\s*(SoftwareSystem|Container|Component|Person)\s+"([^"\\]+)"', re.MULTILINE)
    var_info: dict[str, dict[str, str | None]] = {}
    stack: list[tuple[str, str]] = []
    for line in model_block.splitlines():
        m = decl_re.match(line)
        if m:
            var = m.group(2)
            typ = m.group(3)
            disp = m.group(4)
            parent_system = None
            parent_container = None
            for pvar, ptyp in reversed(stack):
                if parent_system is None and ptyp == 'SoftwareSystem':
                    parent_system = pvar
                if parent_container is None and ptyp == 'Container':
                    parent_container = pvar
                if parent_system and parent_container:
                    break
            var_info[var] = {
                'type': typ,
                'parentSystem': parent_system,
                'parentContainer': parent_container,
                'displayName': disp,
            }
            if '{' in line and '}' not in line:
                stack.append((var, typ))
            continue
        # Track closing braces
        if '}' in line and stack:
            stack.pop()

    # Helper to map display name (optionally System/Container) to variable
    def resolve_name(name: Optional[str]) -> Optional[str]:
        def _norm(s: Optional[str]) -> Optional[str]:
            if s is None:
                return None
            return s.strip().lower().replace('_', '-').replace(' ', '-')

        if not name:
            return '*'
        # System/Container disambiguation with normalization
        if '/' in name:
            sys_name, inner_name = name.split('/', 1)
            n_sys, n_inner = _norm(sys_name), _norm(inner_name)
            # Find matching container by display name under matching system
            for v, info in var_info.items():
                if _norm(info.get('displayName')) == n_inner and info.get('parentSystem'):
                    ps = info.get('parentSystem')
                    if _norm(var_info.get(str(ps), {}).get('displayName')) == n_sys:
                        return v
            # Not found
            return None

        # Single-name resolution by display name (normalized)
        preferred = ['SoftwareSystem', 'Container', 'Component', 'Person']
        n_name = _norm(name)
        candidates: list[tuple[int, str]] = []
        for v, info in var_info.items():
            if _norm(info.get('displayName')) == n_name:
                try:
                    rank = preferred.index(str(info.get('type')))
                except ValueError:
                    rank = len(preferred)
                candidates.append((rank, v))
        if candidates:
            candidates.sort()
            return candidates[0][1]
        # Not found
        return None

    # Iterate views and inject filters right before autoLayout
    lines = dsl.splitlines()
    out: list[str] = []
    in_views = False
    # Maintain separate indices per kind to align with view ordering in DSL
    kind_indices: dict[str, int] = { 'systemContext': -1, 'container': -1, 'component': -1, 'systemLandscape': -1 }
    current_view_has_filters: Optional[list[object]] = None
    current_view_element_excludes: Optional[list[str]] = None
    header_re = re.compile(r'^(\s*)(systemContext|container|component)\s+([A-Za-z0-9_]+)\s*\{')
    landscape_header_re = re.compile(r'^(\s*)systemLandscape\s*\{')
    # Order of landscape views in DSL: non-smart first, then smart landscapes
    try:
        from arch_diagrams.c4 import SystemLandscapeView as _LSV
    except Exception:
        _LSV = None  # type: ignore[assignment]
    landscapes_in_dsl_order = [v for v in non_smart_views if (_LSV and isinstance(v, _LSV))] + smart_landscapes
    for line in lines:
        if line.strip() == 'views {':
            in_views = True
            out.append(line)
            continue
        if not in_views:
            out.append(line)
            continue
        m = header_re.match(line)
        if m:
            _, kind, _subject = m.group(1), m.group(2), m.group(3)
            # Advance index for this kind and select the matching view of same kind
            kind_indices[kind] += 1
            idx = kind_indices[kind]
            # Filter non-smart views by kind in definition order
            def _is_kind(v: object) -> bool:
                from arch_diagrams.c4.model import SystemContextView as MSystemContextView, ContainerView as MContainerView, ComponentView as MComponentView
                if kind == 'systemContext':
                    return isinstance(v, MSystemContextView)
                if kind == 'container':
                    return isinstance(v, MContainerView)
                if kind == 'component':
                    return isinstance(v, MComponentView)
                return False
            views_of_kind = [v for v in non_smart_views if _is_kind(v)]
            if 0 <= idx < len(views_of_kind):
                v = views_of_kind[idx]
                current_view_has_filters = getattr(v, '_name_relationship_filters', None)
                current_view_element_excludes = getattr(v, '_element_excludes_names', None)
            else:
                current_view_has_filters = None
                current_view_element_excludes = None
            out.append(line)
            continue
        mland = landscape_header_re.match(line)
        if mland:
            # systemLandscape header (no subject)
            kind_indices['systemLandscape'] += 1
            idx = kind_indices['systemLandscape']
            v = landscapes_in_dsl_order[idx] if 0 <= idx < len(landscapes_in_dsl_order) else None
            if v is not None:
                current_view_has_filters = getattr(v, '_name_relationship_filters', None)
                current_view_element_excludes = getattr(v, '_element_excludes_names', None)
            else:
                current_view_has_filters = None
                current_view_element_excludes = None
            out.append(line)
            continue
        if in_views and 'autoLayout' in line and (current_view_has_filters or current_view_element_excludes):
            # insert sentinel and filters before autoLayout
            out.append('      //__NAME_FILTERS__')
            # Element-level excludes (exclude <element>)
            if current_view_element_excludes:
                for nm in current_view_element_excludes:
                    v = resolve_name(nm)
                    if v and v != '*':
                        out.append(f"      exclude {v}")
            # Relationship name-based filters
            if current_view_has_filters:
                for nf in current_view_has_filters:
                    if isinstance(nf, IncludeRelByName):
                        from_var = resolve_name(getattr(nf, 'from_name', None))
                        to_var = resolve_name(getattr(nf, 'to_name', None))
                        # Only emit if both sides resolvable (allow wildcard '*')
                        if (from_var == '*' or from_var is not None) and (to_var == '*' or to_var is not None):
                            out.append(f"      include {from_var}->{to_var}")
                    elif isinstance(nf, ExcludeRelByName):
                        from_var = resolve_name(getattr(nf, 'from_name', None))
                        to_var = resolve_name(getattr(nf, 'to_name', None))
                        if (from_var == '*' or from_var is not None) and (to_var == '*' or to_var is not None):
                            out.append(f"      exclude {from_var}->{to_var}")
                        for bi in getattr(nf, 'but_include_names', ()):
                            bi_var = resolve_name(bi)
                            if bi_var is None:
                                continue
                            if getattr(nf, 'from_name', None) and from_var not in (None, '*'):
                                out.append(f"      include {from_var}->{bi_var}")
                            elif to_var not in (None, '*'):
                                out.append(f"      include {bi_var}->{to_var}")
            out.append(line)
            continue
        # Reset state on view closure to avoid leaks into subsequent views
        if in_views and line.strip() == '}':
            current_view_has_filters = None
            current_view_element_excludes = None
            out.append(line)
            continue
        out.append(line)
    return '\n'.join(out)
