from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


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

    def add_element_style(self, style: ElementStyle) -> None:
        self.element_styles.append(style)

    def add_relationship_style(self, style: RelationshipStyle) -> None:
        self.relationship_styles.append(style)
