from __future__ import annotations
from dataclasses import dataclass, field
from collections import OrderedDict
from typing import List, Optional, Set, Iterable
from slugify import slugify

@dataclass
class ElementBase:
    name: str
    description: str = ""
    technology: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    parent: Optional['ElementBase'] = field(default=None, repr=False)
    id: str = field(init=False)

    def __post_init__(self):
        slug = slugify(self.name or "", lowercase=True)
        self.id = slug or "item"

    def full_tags(self) -> List[str]:
        return sorted(self.tags)

    # Pair-building operators for relationships (non-intrusive; no model coupling)
    def __rshift__(self, other: 'ElementBase') -> tuple['ElementBase','ElementBase']:
        return (self, other)
    def __lshift__(self, other: 'ElementBase') -> tuple['ElementBase','ElementBase']:
        # X << Y means Y -> X (source is other, destination is self)
        return (other, self)

@dataclass
class Person(ElementBase):
    pass

@dataclass
class SoftwareSystem(ElementBase):
    # Containers stored in an OrderedDict keyed by name for O(1) lookup and stable order
    _containers: 'OrderedDict[str, Container]' = field(default_factory=OrderedDict, repr=False, init=False)

    @property
    def containers(self) -> List['Container']:
        return list(self._containers.values())

    def add_container(self, name: str, description: str = "", technology: Optional[str] = None, tags: Optional[Iterable[str]] = None) -> 'Container':
        existing = self._containers.get(name)
        if existing:
            if description and not existing.description:
                existing.description = description
            if technology and not existing.technology:
                existing.technology = technology
            if tags:
                # Treat a string as a single tag; otherwise assume iterable of strings
                if isinstance(tags, str):
                    existing.tags.update({tags})
                else:
                    existing.tags.update(tags)
            return existing
        # Normalize tags: string -> singleton set; iterable -> set; None -> empty set
        if isinstance(tags, str):
            tag_set = {tags}
        else:
            tag_set = set(tags or [])
        c = Container(name=name, description=description, technology=technology, tags=tag_set, parent=self)
        self._containers[name] = c
        return c

    # Operator sugar: system + Container(...) attaches/adopts container (idempotent by name)
    # Returns the SoftwareSystem to allow chaining: system + C1 + C2 + C3
    def __add__(self, other: 'Container') -> 'SoftwareSystem':  # type: ignore[override]
        existing = self._containers.get(other.name)
        if existing is None:
            other.parent = self
            # Normalize tags on adopted container: string -> singleton set
            if isinstance(other.tags, str):  # type: ignore[redundant-cast]
                other.tags = {other.tags}  # type: ignore[assignment]
            elif not isinstance(other.tags, set):
                try:
                    other.tags = set(other.tags)  # type: ignore[arg-type,assignment]
                except Exception:
                    other.tags = set()  # type: ignore[assignment]
            self._containers[other.name] = other
        else:
            if other.description and not existing.description:
                existing.description = other.description
            if other.technology and not existing.technology:
                existing.technology = other.technology
            # Merge tags safely (normalize string)
            if isinstance(other.tags, str):  # type: ignore[redundant-cast]
                existing.tags.update({other.tags})
            else:
                try:
                    existing.tags.update(other.tags)  # type: ignore[arg-type]
                except Exception:
                    pass
        return self

    # Allow system["container-name"] access (mirrors previous proxy behavior)
    def __getitem__(self, container_name: str) -> 'Container':
        found = self._containers.get(container_name)
        if not found:
            raise ValueError(f"Expected container '{container_name}' to exist in system '{self.name}'")
        return found


@dataclass
class Container(ElementBase):
    # Components stored in an OrderedDict keyed by name
    _components: 'OrderedDict[str, Component]' = field(default_factory=OrderedDict, repr=False, init=False)

    @property
    def components(self) -> List['Component']:
        return list(self._components.values())

    def add_component(self, name: str, description: str = "", technology: Optional[str] = None, tags: Optional[Iterable[str]] = None) -> 'Component':
        existing = self._components.get(name)
        if existing:
            if description and not existing.description:
                existing.description = description
            if technology and not existing.technology:
                existing.technology = technology
            if tags:
                if isinstance(tags, str):
                    existing.tags.update({tags})
                else:
                    existing.tags.update(tags)
            return existing
        if isinstance(tags, str):
            tag_set = {tags}
        else:
            tag_set = set(tags or [])
        comp = Component(name=name, description=description, technology=technology, tags=tag_set, parent=self)
        self._components[name] = comp
        return comp

@dataclass
class Component(ElementBase):
    pass

# Deployment / Infrastructure
@dataclass
class DeploymentNode(ElementBase):
    children: List['DeploymentNode'] = field(default_factory=list, repr=False)
    infrastructure_nodes: List['InfrastructureNode'] = field(default_factory=list, repr=False)
    software_system_instances: List['SoftwareSystemInstance'] = field(default_factory=list, repr=False)
    container_instances: List['ContainerInstance'] = field(default_factory=list, repr=False)

    def add_deployment_node(self, name: str, description: str = "", technology: Optional[str] = None, tags: Optional[Iterable[str]] = None) -> 'DeploymentNode':
        node = DeploymentNode(name=name, description=description, technology=technology, tags=set(tags or []), parent=self)
        self.children.append(node)
        return node

    def add_infrastructure_node(self, name: str, description: str = "", technology: Optional[str] = None, tags: Optional[Iterable[str]] = None) -> 'InfrastructureNode':
        infra = InfrastructureNode(name=name, description=description, technology=technology, tags=set(tags or []), parent=self)
        self.infrastructure_nodes.append(infra)
        return infra

    def add_software_system_instance(self, software_system: SoftwareSystem, instance_tag: str = "Instance") -> 'SoftwareSystemInstance':
        inst = SoftwareSystemInstance(name=software_system.name, description=software_system.description, technology=software_system.technology, tags=set(software_system.tags), parent=self, software_system=software_system, instance_tag=instance_tag)
        self.software_system_instances.append(inst)
        return inst

    def add_container_instance(self, container: Container, instance_tag: str = "Instance") -> 'ContainerInstance':
        inst = ContainerInstance(name=container.name, description=container.description, technology=container.technology, tags=set(container.tags), parent=self, container=container, instance_tag=instance_tag)
        self.container_instances.append(inst)
        return inst

@dataclass
class InfrastructureNode(ElementBase):
    pass

@dataclass
class SoftwareSystemInstance(ElementBase):
    software_system: 'SoftwareSystem' = field(default=None, repr=False)  # type: ignore[assignment]
    instance_tag: str = "Instance"

@dataclass
class ContainerInstance(ElementBase):
    container: 'Container' = field(default=None, repr=False)  # type: ignore[assignment]
    instance_tag: str = "Instance"

@dataclass
class Relationship:
    source: ElementBase
    destination: ElementBase
    description: str
    technology: Optional[str] = None
    tags: Set[str] = field(default_factory=set)

    def id_tuple(self):
        return (self.source.id, self.destination.id, self.description, self.technology)

class ViewType:
    SYSTEM_LANDSCAPE = "SystemLandscape"
    SYSTEM_CONTEXT = "SystemContext"
    CONTAINER = "Container"
    COMPONENT = "Component"
    DEPLOYMENT = "Deployment"

@dataclass
class ViewBase:
    key: str
    name: str
    view_type: str
    include: Set[str] = field(default_factory=set)  # element ids
    description: str = ""

    def add(self, element: ElementBase):
        self.include.add(element.id)

@dataclass
class SystemLandscapeView(ViewBase):
    pass

@dataclass
class SmartSystemLandscapeView(SystemLandscapeView):
    """System Landscape view that semantically requests wildcard include * plus explicit includes.

    This allows the exporter to render via pystructurizr normally and then add a wildcard line
    without brittle pattern matching across arbitrary views.
    """
    wildcard: bool = True

@dataclass
class SystemContextView(ViewBase):
    software_system: Optional[SoftwareSystem] = None

@dataclass
class ContainerView(ViewBase):
    software_system: Optional[SoftwareSystem] = None

@dataclass
class ComponentView(ViewBase):
    container: Optional[Container] = None

@dataclass
class DeploymentView(ViewBase):
    environment: str = ""

# Styles
@dataclass
class ElementStyle:
    tag: str
    background: Optional[str] = None
    color: Optional[str] = None
    shape: Optional[str] = None
    opacity: Optional[int] = None

@dataclass
class RelationshipStyle:
    tag: str
    color: Optional[str] = None
    dashed: Optional[bool] = None
    thickness: Optional[int] = None

@dataclass
class Styles:
    element_styles: List[ElementStyle] = field(default_factory=list)
    relationship_styles: List[RelationshipStyle] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)

    def add_element_style(self, style: ElementStyle):
        self.element_styles.append(style)

    def add_relationship_style(self, style: RelationshipStyle):
        self.relationship_styles.append(style)

"""Former base model removed; functionality merged into SystemLandscape (see system_landscape.py)."""
