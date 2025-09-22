from typing import Optional

from pystructurizr.dsl import Dumper, Element, View

from architecture_diagrams.extensions.relationships import RelationshipFilter


DEFAULT_VIEW_TAG = "default"
TD_VIEW_TAG = "td"


class SmartView(View):  # type: ignore[misc]
    def __init__(
        self,
        viewkind: View.Kind,
        element: Element,
        name: str,
        description: Optional[str] = None,
        tag: Optional[str] = None,
    ):
        self.viewkind = viewkind
        self.element = element
        self.name = name
        self.description = description
        self.tag = tag
        self.includes: list[Element] = []
        self.excludes: list[Element] = []

    def include(self, element: Element) -> "View":
        self.includes.append(element)
        return self

    def exclude(self, element: Element) -> "View":
        self.excludes.append(element)
        return self

    def dump(self, dumper: Dumper) -> None:
        # pystructurizr uses lowercase kind names in dump (e.g., systemLandscape); ensure parity
        kind = self.viewkind.value[0].lower() + self.viewkind.value[1:]
        dumper.add(
            f'{kind} {self.element.instname if self.element else ""} {{'
        )
        dumper.indent()
        if self.description:
            dumper.add(f'description "{self.description}"')
        # Only include everything when the view hasn't specified explicit element includes.
        # This lets curated smart views show a subset of elements rather than the whole model.
        has_explicit_includes = any(not isinstance(e, RelationshipFilter) for e in self.includes)
        if not has_explicit_includes:
            dumper.add("include *")
        for include in self.includes:
            if isinstance(include, RelationshipFilter):
                include.dump(dumper)
            else:
                dumper.add(f"include {include.instname}")
        for exclude in self.excludes:
            if isinstance(exclude, RelationshipFilter):
                exclude.dump(dumper)
            else:
                dumper.add(f"exclude {exclude.instname}")
        dumper.add("autoLayout")
        dumper.outdent()
        dumper.add("}")
