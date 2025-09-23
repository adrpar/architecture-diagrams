"""Unified SystemLandscape class (formerly WorkspaceModel + registry merged)."""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
    overload,
)

from .model import (
    ComponentView,
    Container,
    ContainerView,
    DeploymentNode,
    DeploymentView,
    ElementBase,
    Person,
    Relationship,
    SmartSystemLandscapeView,
    SoftwareSystem,
    Styles,
    SystemContextView,
    SystemLandscapeView,
    ViewType,
)

# _SLSystemProxy removed; SystemLandscape.__getitem__ now returns SoftwareSystem directly.


class SystemLandscape:
    """Unified architectural model + registry semantics.

    This physically merges the previous separate model functionality with the
    registry/indexing ergonomics. The former ``WorkspaceModel`` has been removed from the
    public API; all callers should use SystemLandscape directly.
    """

    def __init__(self, name: str, description: str = "") -> None:
        # Core metadata
        self.name = name
        self.description = description
        # Element stores
        self.people: Dict[str, Person] = {}
        self.software_systems: Dict[str, SoftwareSystem] = {}
        self.groups: Dict[str, List[SoftwareSystem]] = {}
        self.deployment_nodes: Dict[str, DeploymentNode] = {}
        self.relationships: List[Relationship] = []
        self.views: List[
            SystemLandscapeView
            | SystemContextView
            | ContainerView
            | ComponentView
            | DeploymentView
            | SmartSystemLandscapeView
        ] = []
        self.styles = Styles()
        # ID tracking / uniqueness
        self._all_ids: Set[str] = set()
        # Relationship restriction / filtering
        self._allowed_relationship_pairs: Optional[Set[tuple[str, str]]] = None
        self._relationship_identity: Set[tuple[str, str, str, Optional[str]]] = set()
        # Registry style container index
        self._containers_index: Dict[tuple[str, str], Container] = {}

    # ----- Element creation helpers -----
    def add_person(self, name: str, description: str = "", **kwargs: Any) -> Person:
        tags = set(kwargs.get("tags", []))
        p = Person(name=name, description=description, tags=tags)
        self._register(p)
        self.people[p.id] = p
        return p

    def add_software_system(
        self, name: str, description: str = "", **kwargs: Any
    ) -> SoftwareSystem:
        existing = next((s for s in self.software_systems.values() if s.name == name), None)
        if existing:
            if description and not existing.description:
                existing.description = description
            if kwargs.get("technology") and not existing.technology:
                existing.technology = kwargs.get("technology")
            existing.tags.update(kwargs.get("tags", []))
            # Ensure index refreshed
            for c in existing.containers:
                self._containers_index[(existing.name, c.name)] = c
            return existing
        s = SoftwareSystem(
            name=name,
            description=description,
            technology=kwargs.get("technology"),
            tags=set(kwargs.get("tags", [])),
        )
        self._register(s)
        self.software_systems[s.id] = s
        for c in s.containers:
            self._containers_index[(s.name, c.name)] = c
        return s

    def assign_group(self, group_name: str, system: SoftwareSystem):
        self.groups.setdefault(group_name, []).append(system)

    def add_deployment_node(
        self, name: str, description: str = "", **kwargs: Any
    ) -> DeploymentNode:
        node = DeploymentNode(
            name=name,
            description=description,
            technology=kwargs.get("technology"),
            tags=set(kwargs.get("tags", [])),
        )
        self._register(node)
        self.deployment_nodes[node.id] = node
        return node

    def add_relationship(
        self,
        source: ElementBase,
        destination: ElementBase,
        description: str,
        technology: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
    ) -> Relationship:
        ident = (source.name, destination.name, description, technology)
        if ident in self._relationship_identity:
            for r in reversed(self.relationships):
                if (r.source.name, r.destination.name, r.description, r.technology) == ident:
                    return r
        rel = Relationship(
            source=source,
            destination=destination,
            description=description,
            technology=technology,
            tags=set(tags or []),
        )
        self.relationships.append(rel)
        self._relationship_identity.add(ident)
        return rel

    # ----- Relationship filtering -----
    def restrict_relationships_to(self, allowed_pairs: Set[tuple[str, str]]):
        self._allowed_relationship_pairs = {(s, d) for s, d in allowed_pairs}

    def clear_relationship_restrictions(self):  # pragma: no cover - simple setter
        self._allowed_relationship_pairs = None

    def get_effective_relationships(self) -> Iterable[Relationship]:  # type: ignore[override]
        if self._allowed_relationship_pairs is None:
            return list(self.relationships)
        allowed = self._allowed_relationship_pairs
        return [r for r in self.relationships if (r.source.name, r.destination.name) in allowed]

    def add_container(
        self,
        system_name: str,
        name: str,
        description: str = "",
        technology: str | None = None,
        tags: Optional[Iterable[str]] = None,
    ) -> Container:
        system = self.get_system(system_name)
        c = system.add_container(name, description, technology, tags)
        self._containers_index[(system.name, c.name)] = c
        return c

    # ----- Views -----
    def add_system_landscape_view(
        self, key: str, name: str, description: str = ""
    ) -> SystemLandscapeView:
        v = SystemLandscapeView(
            key=key, name=name, view_type=ViewType.SYSTEM_LANDSCAPE, description=description
        )
        self.views.append(v)
        return v

    def add_smart_system_landscape_view(self, key: str, name: str, description: str = "") -> SmartSystemLandscapeView:  # type: ignore[name-defined]
        v = SmartSystemLandscapeView(key=key, name=name, view_type=ViewType.SYSTEM_LANDSCAPE, description=description)  # type: ignore[name-defined]
        self.views.append(v)
        return v

    def add_system_context_view(
        self, key: str, name: str, software_system: SoftwareSystem, description: str = ""
    ) -> SystemContextView:
        v = SystemContextView(
            key=key,
            name=name,
            view_type=ViewType.SYSTEM_CONTEXT,
            software_system=software_system,
            description=description,
        )
        self.views.append(v)
        return v

    def add_container_view(
        self, key: str, name: str, software_system: SoftwareSystem, description: str = ""
    ) -> ContainerView:
        v = ContainerView(
            key=key,
            name=name,
            view_type=ViewType.CONTAINER,
            software_system=software_system,
            description=description,
        )
        self.views.append(v)
        return v

    def add_component_view(
        self, key: str, name: str, container: Container, description: str = ""
    ) -> ComponentView:
        v = ComponentView(
            key=key,
            name=name,
            view_type=ViewType.COMPONENT,
            container=container,
            description=description,
        )
        self.views.append(v)
        return v

    def add_deployment_view(
        self, key: str, name: str, environment: str = "", description: str = ""
    ) -> DeploymentView:
        v = DeploymentView(
            key=key,
            name=name,
            view_type=ViewType.DEPLOYMENT,
            environment=environment,
            description=description,
        )
        self.views.append(v)
        return v

    # ----- ID registration -----
    def _register(self, element: ElementBase):
        base_id = element.id
        if base_id in self._all_ids:
            i = 2
            while f"{base_id}-{i}" in self._all_ids:
                i += 1
            element.id = f"{base_id}-{i}"
        self._all_ids.add(element.id)

    # ----- Iteration over all elements -----
    def iter_elements(
        self,
    ) -> Iterable[ElementBase]:  # pragma: no cover - traversal logic covered indirectly
        for p in self.people.values():
            yield p
        for s in self.software_systems.values():
            yield s
            for c in s.containers:
                yield c
                for comp in c.components:
                    yield comp
        for d in self.deployment_nodes.values():
            yield d
            for inf in d.infrastructure_nodes:
                yield inf
            for ssi in d.software_system_instances:
                yield ssi
            for ci in d.container_instances:
                yield ci
            stack = list(d.children)
            while stack:
                child = stack.pop()
                yield child
                for inf in child.infrastructure_nodes:
                    yield inf
                for ssi in child.software_system_instances:
                    yield ssi
                for ci in child.container_instances:
                    yield ci
                stack.extend(child.children)

    # ----- Registry-style accessors -----
    def get_system(self, name: str) -> SoftwareSystem:  # name-based (not slug) retrieval
        existing = next((s for s in self.software_systems.values() if s.name == name), None)
        if not existing:
            raise ValueError(f"Expected software system '{name}' to be defined before access")
        return existing

    def get_container(self, system_name: str, container_name: str) -> Container:
        key = (system_name, container_name)
        if key in self._containers_index:
            return self._containers_index[key]
        system = self.get_system(system_name)
        found = next((c for c in system.containers if c.name == container_name), None)
        if not found:
            raise ValueError(
                f"Expected container '{container_name}' to exist in system '{system_name}'"
            )
        # Backfill index for future fast lookup
        self._containers_index[key] = found
        return found

    def get_person(self, name: str) -> Person:
        """Return a Person by name or raise ValueError if not yet defined.

        Mirrors get_system semantics for consistency with previous helper style.
        """
        existing = next((p for p in self.people.values() if p.name == name), None)
        if not existing:
            raise ValueError(f"Expected person '{name}' to be defined before access")
        return existing

    @overload
    def __getitem__(self, key: str) -> SoftwareSystem: ...  # system lookup
    @overload
    def __getitem__(self, key: Tuple[str, str]) -> Container: ...  # (system, container)
    def __getitem__(self, key: Union[str, Tuple[str, str]]):  # type: ignore[override]
        if isinstance(key, tuple):
            sys_name, cont_name = key
            return self.get_container(sys_name, cont_name)
        if "/" in key:
            sys_name, cont_name = key.split("/", 1)
            return self.get_container(sys_name, cont_name)
        # Person lookup prefix: model['person:User']
        if key.startswith("person:"):
            return self.get_person(key.split(":", 1)[1])
        return self.get_system(key)

    def __contains__(self, key: Union[str, Tuple[str, str]]) -> bool:  # type: ignore[override]
        if isinstance(key, tuple):
            return key in self._containers_index
        if "/" in key:
            parts = key.split("/", 1)
            if len(parts) == 2:
                return (parts[0], parts[1]) in self._containers_index
        return any(s.name == key for s in self.software_systems.values())

    def __iter__(self) -> Iterator[str]:  # pragma: no cover
        return (s.name for s in self.software_systems.values())

    # Operator sugar: landscape << system
    def __lshift__(self, other: SoftwareSystem) -> "SystemLandscape":
        # Ensure uniqueness via add_software_system semantics
        self.add_software_system(
            other.name, other.description, technology=other.technology, tags=other.tags
        )
        # Merge containers from provided system (adopt pattern)
        for c in other.containers:
            self.add_container(other.name, c.name, c.description, c.technology, c.tags)
        return self

    # Operator sugar: landscape + SoftwareSystem(...) mirrors << but allows inline literal construction.
    # Extended to also accept Person instances for symmetry (idempotent by Person.name).
    # Enables chaining: model + SoftwareSystem("A") + Person("User")
    def __add__(self, other: Any):  # type: ignore[override]
        # Accept SoftwareSystem or Person; raise for anything else.
        if isinstance(other, SoftwareSystem):
            return self.__lshift__(other)
        if isinstance(other, Person):
            # Idempotent person registration by name
            if not any(p.name == other.name for p in self.people.values()):
                self.add_person(other.name, other.description, tags=other.tags)
            return self
        raise TypeError(
            f"Unsupported operand type(s) for +: 'SystemLandscape' and '{type(other).__name__}'"
        )

    # Relationship sugar (pair or src,dst forms)
    def relate(self, *args: Any):
        src: ElementBase
        dst: ElementBase
        if len(args) == 2:
            pair, spec = args  # type: ignore[assignment]
            if not isinstance(pair, tuple) or len(cast(tuple[Any, Any], pair)) != 2:
                raise TypeError("First argument must be (src,dst) tuple when using 2-arg form")
            # Narrow types explicitly
            pair_t = cast(tuple[Any, Any], pair)
            raw_src = pair_t[0]
            raw_dst = pair_t[1]
            if not isinstance(raw_src, ElementBase) or not isinstance(raw_dst, ElementBase):
                raise TypeError("Tuple must contain ElementBase instances")
            src, dst = raw_src, raw_dst
        elif len(args) == 3:
            raw_src, raw_dst, spec = args
            if not isinstance(raw_src, ElementBase) or not isinstance(raw_dst, ElementBase):
                raise TypeError("src and dst must be ElementBase instances")
            src, dst = raw_src, raw_dst
        else:
            raise TypeError("relate expects (pair, spec) or (src, dst, spec)")
        if isinstance(spec, str):
            return self.add_relationship(src, dst, spec)
        if not isinstance(spec, (list, tuple)):
            raise TypeError("spec must be str or sequence")
        seq = cast(Sequence[Any], spec)
        desc = seq[0] if len(seq) > 0 else ""
        tech = seq[1] if len(seq) > 1 else None
        tags = seq[2] if len(seq) > 2 else None
        if not isinstance(desc, str) or not desc:
            raise ValueError("Relationship description cannot be empty")
        return self.add_relationship(src, dst, desc, tech, tags)

    # Backwards compat alias
    rel = relate

    # Convenience property for external inspection
    @property
    def relationships_list(self) -> Iterable[Relationship]:  # pragma: no cover
        return self.relationships

    # ----- Overlay helpers -----
    def replace_container(
        self,
        system_name: str,
        old_name: str,
        new_name: str,
        *,
        description: str = "",
        technology: Optional[str] = None,
        tag_new: Optional[Iterable[str]] = None,
        tag_old: Optional[Iterable[str]] = None,
        remove_old: bool = True,
    ) -> None:
        """Create/ensure a new container and rewire relationships away from an old one.

        - Ensures `new_name` container exists under the system (adds if missing)
        - Rewrites all relationships where source or destination is the old container to point to the new one
        - Optionally tags the new and/or old containers
        - Optionally removes the old container from the system and container index
        """
        system = self.get_system(system_name)
        # Ensure new container exists
        new_c = system.add_container(new_name, description, technology, tags=tag_new or [])
        self._containers_index[(system.name, new_c.name)] = new_c

        old_c = None
        try:
            old_c = self.get_container(system_name, old_name)
        except Exception:
            old_c = None

        if old_c is not None and tag_old:
            old_c.tags.update(set(tag_old))

        if old_c is not None and old_c is not new_c:
            # Rewire relationships and update identity set
            updated_identities: list[
                tuple[tuple[str, str, str, Optional[str]], tuple[str, str, str, Optional[str]]]
            ] = []
            for rel in self.relationships:
                old_ident = (rel.source.name, rel.destination.name, rel.description, rel.technology)
                changed = False
                if rel.source is old_c:
                    rel.source = new_c
                    changed = True
                if rel.destination is old_c:
                    rel.destination = new_c
                    changed = True
                if changed:
                    new_ident = (
                        rel.source.name,
                        rel.destination.name,
                        rel.description,
                        rel.technology,
                    )
                    updated_identities.append((old_ident, new_ident))
            # Refresh identity set entries
            for old_ident, new_ident in updated_identities:
                if old_ident in self._relationship_identity:
                    self._relationship_identity.discard(old_ident)
                self._relationship_identity.add(new_ident)

            # Optionally remove old container
            if remove_old:
                try:
                    # Remove from system container map
                    if hasattr(system, "_containers"):
                        system._containers.pop(old_name, None)  # type: ignore[attr-defined]
                    # Remove from index
                    self._containers_index.pop((system.name, old_name), None)
                except Exception:
                    # Best-effort removal; keep running even if internal
                    pass


__all__ = ["SystemLandscape"]
