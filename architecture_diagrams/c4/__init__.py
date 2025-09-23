"""Internal, tool-agnostic C4 domain model.

This layer defines pure Python classes representing C4 model concepts.
They are intentionally decoupled from pystructurizr so we can map them to
other exporters in the future (PlantUML, JSON, etc.).
"""

from .model import (
    Component,
    Container,
    ContainerInstance,
    DeploymentNode,
    ElementBase,
    InfrastructureNode,
    Person,
    Relationship,
    SoftwareSystem,
    SoftwareSystemInstance,
)
from .styles import ElementStyle, RelationshipStyle, Styles
from .system_landscape import SystemLandscape
from .views import (
    ComponentView,
    ContainerView,
    DeploymentView,
    SystemContextView,
    SystemLandscapeView,
    ViewType,
)

__all__ = [
    "ElementBase",
    "Person",
    "SoftwareSystem",
    "Container",
    "Component",
    "DeploymentNode",
    "InfrastructureNode",
    "SoftwareSystemInstance",
    "ContainerInstance",
    "Relationship",
    "SystemContextView",
    "ContainerView",
    "ComponentView",
    "SystemLandscapeView",
    "DeploymentView",
    "Styles",
    "ElementStyle",
    "RelationshipStyle",
    "ViewType",
    "SystemLandscape",
]
