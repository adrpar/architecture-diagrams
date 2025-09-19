"""Legacy helper for attaching a Smart System Landscape view.

Deprecated: prefer `SystemLandscape.add_smart_system_landscape_view()` and adding includes
directly to the returned view. This function remains for backward compatibility.
"""
from __future__ import annotations
from typing import Iterable, Union
from arch_diagrams.c4.model import ElementBase, SoftwareSystem
from arch_diagrams.c4.system_landscape import SystemLandscape

def attach_smart_system_landscape(model: SystemLandscape, name: str, description: str, includes: Iterable[Union[str, ElementBase, SoftwareSystem]]):  # pragma: no cover - legacy path
    include_ids: list[str] = []
    for inc in includes:
        if isinstance(inc, str):
            candidate = next((s for s in model.software_systems.values() if s.name == inc), None)
            if candidate:
                include_ids.append(candidate.id)
        else:
            include_ids.append(inc.id)
    model._smart_system_landscape = {  # type: ignore[attr-defined]
        "name": name,
        "description": description,
        "includes": include_ids,
    }
    return model
