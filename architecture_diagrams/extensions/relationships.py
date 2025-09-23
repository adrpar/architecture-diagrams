from enum import Enum
from typing import Optional

from pystructurizr.dsl import Dumper, Element


class RelationshipFilter(Element):  # type: ignore[misc]
    class FilterType(Enum):
        INCLUDE = "include"
        EXCLUDE = "exclude"

    def __init__(
        self,
        type: FilterType,
        from_element: Optional[Element] = None,
        to_element: Optional[Element] = None,
        but_include_elements: Optional[list[Element]] = None,
    ):
        self.from_string = from_element.instname if from_element else "*"
        self.to_string = to_element.instname if to_element else "*"

        super().__init__(name=f"filter-{self.from_string}-{self.to_string}")

        self.type = type
        self.from_element = from_element
        self.to_element = to_element
        self.but_include_elements = (
            but_include_elements
            if (but_include_elements and type == RelationshipFilter.FilterType.EXCLUDE)
            else None
        )

    def dump(self, dumper: Dumper) -> None:
        dumper.add(f"{self.type.value} {self.from_string}->{self.to_string}")

        if self.but_include_elements and self.type == RelationshipFilter.FilterType.EXCLUDE:
            for element in self.but_include_elements:
                if self.from_element:
                    dumper.add(f"include {self.from_string}->{element.instname}")
                else:
                    dumper.add(f"include {element.instname}->{self.to_string}")
