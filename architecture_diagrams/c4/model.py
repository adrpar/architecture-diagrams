from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Set

from slugify import slugify


@dataclass
class ElementBase:
    name: str
    description: str = ""
    technology: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    parent: Optional["ElementBase"] = field(default=None, repr=False)
    id: str = field(init=False)

    def __post_init__(self):
        slug = slugify(self.name or "", lowercase=True)
        self.id = slug or "item"

    def full_tags(self) -> List[str]:
        return sorted(self.tags)

    # Pair-building operators for relationships (non-intrusive; no model coupling)
    def __rshift__(self, other: "ElementBase") -> tuple["ElementBase", "ElementBase"]:
        return (self, other)

    def __lshift__(self, other: "ElementBase") -> tuple["ElementBase", "ElementBase"]:
        # X << Y means Y -> X (source is other, destination is self)
        return (other, self)

    def _normalize_tags(self, tags: Optional[Iterable[str] | str]) -> Set[str]:
        if tags is None:
            return set()
        if isinstance(tags, str):
            return {tags}
        try:
            return set(tags)
        except Exception:
            return set()


@dataclass
class Person(ElementBase):
    pass


@dataclass
class SoftwareSystem(ElementBase):
    _containers: "OrderedDict[str, Container]" = field(
        default_factory=OrderedDict, repr=False, init=False
    )

    @property
    def containers(self) -> List["Container"]:
        return list(self._containers.values())

    def add_container(
        self,
        name: str,
        description: str = "",
        technology: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
    ) -> "Container":
        # Normalize tags once for both update and create paths
        tag_set = self._normalize_tags(tags)
        existing = self._containers.get(name)
        if existing:
            if description and not existing.description:
                existing.description = description
            if technology and not existing.technology:
                existing.technology = technology
            if tag_set:
                existing.tags.update(tag_set)
            return existing
        container = Container(
            name=name, description=description, technology=technology, tags=tag_set, parent=self
        )
        self._containers[name] = container
        return container

    # Operator sugar: system + Container(...) attaches/adopts container (idempotent by name)
    # Returns the SoftwareSystem to allow chaining: system + C1 + C2 + C3
    def __add__(self, other: "Container") -> "SoftwareSystem":  # type: ignore[override]
        # Delegate to add_container for consistent create/update behavior and tag normalization
        self.add_container(
            name=other.name,
            description=other.description,
            technology=other.technology,
            tags=other.tags,
        )
        return self

    # Allow system["container-name"] access (mirrors previous proxy behavior)
    def __getitem__(self, container_name: str) -> "Container":
        found = self._containers.get(container_name)
        if not found:
            raise ValueError(
                f"Expected container '{container_name}' to exist in system '{self.name}'"
            )
        return found


@dataclass
class Container(ElementBase):
    # Components stored in an OrderedDict keyed by name
    _components: "OrderedDict[str, Component]" = field(
        default_factory=OrderedDict, repr=False, init=False
    )

    @property
    def components(self) -> List["Component"]:
        return list(self._components.values())

    def add_component(
        self,
        name: str,
        description: str = "",
        technology: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
    ) -> "Component":
        # Normalize tags once for both update and create paths
        tag_set = self._normalize_tags(tags)
        existing = self._components.get(name)
        if existing:
            if description and not existing.description:
                existing.description = description
            if technology and not existing.technology:
                existing.technology = technology
            if tag_set:
                existing.tags.update(tag_set)
            return existing
        comp = Component(
            name=name, description=description, technology=technology, tags=tag_set, parent=self
        )
        self._components[name] = comp
        return comp


@dataclass
class Component(ElementBase):
    pass


# Deployment / Infrastructure
@dataclass
class DeploymentNode(ElementBase):
    children: List["DeploymentNode"] = field(default_factory=list, repr=False)
    infrastructure_nodes: List["InfrastructureNode"] = field(default_factory=list, repr=False)
    software_system_instances: List["SoftwareSystemInstance"] = field(
        default_factory=list, repr=False
    )
    container_instances: List["ContainerInstance"] = field(default_factory=list, repr=False)

    def add_deployment_node(
        self,
        name: str,
        description: str = "",
        technology: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
    ) -> "DeploymentNode":
        node = DeploymentNode(
            name=name,
            description=description,
            technology=technology,
            tags=self._normalize_tags(tags),
            parent=self,
        )
        self.children.append(node)
        return node

    def add_infrastructure_node(
        self,
        name: str,
        description: str = "",
        technology: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
    ) -> "InfrastructureNode":
        infra = InfrastructureNode(
            name=name,
            description=description,
            technology=technology,
            tags=self._normalize_tags(tags),
            parent=self,
        )
        self.infrastructure_nodes.append(infra)
        return infra

    def add_software_system_instance(
        self, software_system: SoftwareSystem, instance_tag: str = "Instance"
    ) -> "SoftwareSystemInstance":
        inst = SoftwareSystemInstance(
            name=software_system.name,
            description=software_system.description,
            technology=software_system.technology,
            tags=set(software_system.tags),
            parent=self,
            software_system=software_system,
            instance_tag=instance_tag,
        )
        self.software_system_instances.append(inst)
        return inst

    def add_container_instance(
        self, container: Container, instance_tag: str = "Instance"
    ) -> "ContainerInstance":
        inst = ContainerInstance(
            name=container.name,
            description=container.description,
            technology=container.technology,
            tags=set(container.tags),
            parent=self,
            container=container,
            instance_tag=instance_tag,
        )
        self.container_instances.append(inst)
        return inst


@dataclass
class InfrastructureNode(ElementBase):
    pass


@dataclass
class SoftwareSystemInstance(ElementBase):
    software_system: "SoftwareSystem" = field(default=None, repr=False)  # type: ignore[assignment]
    instance_tag: str = "Instance"


@dataclass
class ContainerInstance(ElementBase):
    container: "Container" = field(default=None, repr=False)  # type: ignore[assignment]
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
