"""Internal, tool-agnostic C4 domain model.

This layer defines pure Python classes representing C4 model concepts.
They are intentionally decoupled from pystructurizr so we can map them to
other exporters in the future (PlantUML, JSON, etc.).
"""
from .model import (
    Person,
    SoftwareSystem,
    Container,
    Component,
    DeploymentNode,
    InfrastructureNode,
    SoftwareSystemInstance,
    ContainerInstance,
    Relationship,
    SystemContextView,
    ContainerView,
    ComponentView,
    SystemLandscapeView,
    SmartSystemLandscapeView,
    DeploymentView,
    Styles,
    ElementStyle,
    RelationshipStyle,
    ViewType,
)
from .system_landscape import SystemLandscape

__all__ = [
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
    "SmartSystemLandscapeView",
    "DeploymentView",
    "Styles",
    "ElementStyle",
    "RelationshipStyle",
    "ViewType",
    "SystemLandscape",
]
