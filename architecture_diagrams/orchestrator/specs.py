from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional, Sequence, Set, Union, Protocol, List, cast

from architecture_diagrams.c4.model import ElementBase
from architecture_diagrams.c4.system_landscape import SystemLandscape
from architecture_diagrams.extensions.relationships import RelationshipFilter

Selector = Union[
    str,
    Callable[[SystemLandscape], Iterable[Union[ElementBase, RelationshipFilter]]],
    RelationshipFilter,
]


@dataclass(frozen=True)
class IncludeRelByName:
    from_name: Optional[str] = None  # None => "*"
    to_name: Optional[str] = None    # None => "*"


@dataclass(frozen=True)
class ExcludeRelByName:
    from_name: Optional[str] = None
    to_name: Optional[str] = None
    but_include_names: Sequence[str] = ()  # Only meaningful for exclude


def _empty_tags() -> Set[str]:
    return set()


def _empty_selectors() -> List[Selector]:
    return []

class ViewResolver(Protocol):
    def __call__(self, model: SystemLandscape) -> None: ...

@dataclass
class ViewSpec:
    key: str
    name: str
    view_type: str
    description: str = ""
    tags: Set[str] = field(default_factory=_empty_tags)
    includes: Sequence[Selector] = field(default_factory=_empty_selectors)
    excludes: Sequence[Selector] = field(default_factory=_empty_selectors)  # supports RelationshipFilter and element names for exclusion
    # new explicit relationship filters by display names
    filters: Sequence[Union[IncludeRelByName, ExcludeRelByName]] = field(default_factory=lambda: [])
    subject: Optional[str] = None  # e.g., "System" or "System/Container" for context/container/component views
    smart: bool = False  # Smart landscape view => include *

    def build(self, model: SystemLandscape) -> None:
        # Create the view on the model and resolve includes/excludes
        from architecture_diagrams.c4.model import ViewType
        view = None
        if self.smart and self.view_type == ViewType.SYSTEM_LANDSCAPE:
            view = model.add_smart_system_landscape_view(self.key, self.name, self.description)
        elif self.view_type == ViewType.SYSTEM_LANDSCAPE:
            view = model.add_system_landscape_view(self.key, self.name, self.description)
        elif self.view_type == ViewType.SYSTEM_CONTEXT:
            if not self.subject:
                raise ValueError(f"SystemContext view '{self.key}' requires subject (system name)")
            ss = model.get_system(self.subject)
            view = model.add_system_context_view(self.key, self.name, ss, self.description)
        elif self.view_type == ViewType.CONTAINER:
            if not self.subject or "/" not in self.subject:
                raise ValueError(f"Container view '{self.key}' requires subject in 'System/Container' form")
            sys_name, _ = self.subject.split("/", 1)
            ss = model.get_system(sys_name)
            view = model.add_container_view(self.key, self.name, ss, self.description)
        elif self.view_type == ViewType.COMPONENT:
            if not self.subject or "/" not in self.subject:
                raise ValueError(f"Component view '{self.key}' requires subject in 'System/Container' form")
            sys_name, cont_name = self.subject.split("/", 1)
            c = model.get_container(sys_name, cont_name)
            view = model.add_component_view(self.key, self.name, c, self.description)
        else:
            raise ValueError(f"Unsupported view type: {self.view_type}")

        # Resolve selectors to element ids or RelationshipFilter instances
        def resolve(sel: Selector) -> List[Union[ElementBase, RelationshipFilter]]:
            if isinstance(sel, str):
                s = cast(str, sel)
                if s.startswith("person:"):
                    return [model.get_person(s.split(":",1)[1])]
                if "/" in s:
                    sys_name, cont_name = s.split("/", 1)
                    try:
                        return [model.get_container(sys_name, cont_name)]
                    except Exception:
                        # Could also be System/Component in future
                        pass
                # assume software system by name
                return [model.get_system(s)]
            if isinstance(sel, RelationshipFilter):
                return [sel]
            # callable selector
            func = sel  # type: ignore[assignment]
            res = list(func(model))  # type: ignore[misc]
            return res

        # For non-smart views, we store element IDs in the C4 view include set.
        # For smart views, the exporter will wrap them in extensions.smart_views.SmartView.
        for sel in self.includes:
            for item in resolve(sel):
                if hasattr(item, 'id'):
                    # For system landscape views, containers are not valid include targets.
                    # If a container was selected (e.g., "System/Container"), include its parent Software System instead.
                    try:
                        from architecture_diagrams.c4.model import ViewType as _VT  # local import to avoid module-level cycles
                    except Exception:
                        _VT = None  # type: ignore[assignment]
                    target = item
                    if _VT is not None and self.view_type == _VT.SYSTEM_LANDSCAPE:
                        parent = getattr(item, 'parent', None)
                        # Heuristic: containers have a parent that has a 'containers' attribute
                        if parent is not None and hasattr(parent, 'containers'):
                            target = parent
                    view.add(target)  # type: ignore[attr-defined]
                else:
                    # RelationshipFilter; we cannot add it to C4 ViewBase directly, will be handled at export time for smart views
                    # For standard views this is unsupported and will be ignored silently
                    pass
        # Capture raw excludes to attach to the view for exporter-time injection
        rel_filters: List[RelationshipFilter] = []
        element_exclude_names: List[str] = []
        for sel in self.excludes:
            if isinstance(sel, RelationshipFilter):
                rel_filters.append(sel)
            elif isinstance(sel, str):
                # Capture element-level excludes by display name; exporter will resolve to variables
                element_exclude_names.append(sel)
        # Stash filters on the view for later access by exporter (duck-typed attributes)
        setattr(view, '_relationship_filters', rel_filters)
        if self.filters:
            setattr(view, '_name_relationship_filters', list(self.filters))
        if element_exclude_names:
            setattr(view, '_element_excludes_names', list(element_exclude_names))

__all__ = ["ViewSpec", "Selector", "IncludeRelByName", "ExcludeRelByName"]
