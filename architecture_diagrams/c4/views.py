from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Set

from .model import Container, ElementBase, SoftwareSystem


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

    def add(self, element: ElementBase) -> None:
        self.include.add(element.id)


@dataclass
class SystemLandscapeView(ViewBase):
    # If True, exporters should include all elements allowed by this view type by default,
    # in addition to any explicit includes (Structurizr DSL maps this to 'include *').
    include_all: bool = False


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
