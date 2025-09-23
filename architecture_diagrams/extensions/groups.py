from dataclasses import dataclass, field
from typing import Type

from pystructurizr.dsl import Group as DslGroup, SoftwareSystem


@dataclass
class Group(DslGroup):  # type: ignore[misc]
    elements: dict[str, SoftwareSystem] = field(default_factory=dict)

    def __init__(self, name: str):
        super().__init__(name)
        self.elements = {}

    def add(self, name: str, element: SoftwareSystem) -> None:
        self.elements[name] = element

    def to_dsl_group(self):
        group = DslGroup(self.name)
        group.elements = self.elements.values()
        return group


@dataclass
class Groups(object):
    groups: dict[str, Group] = field(default_factory=dict)

    def add_to_group(self, group_name: str, software_system: SoftwareSystem) -> None:
        if group_name not in self.groups:
            self.groups[group_name] = Group(group_name)

        self.groups[group_name].add(software_system.name, software_system)


class GroupsSingleton(Groups):
    _instance = None

    def __new__(cls: Type["GroupsSingleton"]) -> "GroupsSingleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance
