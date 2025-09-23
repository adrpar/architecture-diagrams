from __future__ import annotations

import json
from typing import Any

from architecture_diagrams.adapter.pystructurizr_export import dump_dsl as structurizr_dump
from architecture_diagrams.plugins import register_exporter


def _as_json_graph(model: Any) -> str:
    """Very simple JSON graph exporter to support alternative outputs and tests.

    Shape:
    {
      "name": <workspace name>,
      "people": [{"name":..., "description":..., "tags": [...] }, ...],
      "systems": [
         {"name":..., "description":..., "tags": [...], "containers": [
             {"name":..., "technology":..., "tags": [...], "components": [...]}
         ]}
      ],
      "relationships": [{"source": <name>, "destination": <name>, "description": ...}, ...]
    }
    """

    def tags_of(obj: Any) -> list[str]:
        t = getattr(obj, "tags", None)
        try:
            return sorted(list(set(t))) if t else []
        except Exception:
            return []

    data: dict[str, Any] = {
        "name": getattr(model, "name", "workspace"),
        "people": [
            {"name": p.name, "description": p.description, "tags": tags_of(p)}
            for p in getattr(model, "people", {}).values()
        ],
        "systems": [],
        "relationships": [],
    }
    for s in getattr(model, "software_systems", {}).values():
        s_obj: dict[str, Any] = {
            "name": s.name,
            "description": s.description,
            "tags": tags_of(s),
            "containers": [],
        }
        for c in getattr(s, "containers", []):
            c_obj: dict[str, Any] = {
                "name": c.name,
                "description": c.description,
                "technology": getattr(c, "technology", ""),
                "tags": tags_of(c),
                "components": [
                    {
                        "name": cm.name,
                        "description": cm.description,
                        "technology": getattr(cm, "technology", ""),
                        "tags": tags_of(cm),
                    }
                    for cm in getattr(c, "components", [])
                ],
            }
            s_obj["containers"].append(c_obj)
        data["systems"].append(s_obj)

    for r in getattr(model, "relationships", []):
        try:
            data["relationships"].append(
                {
                    "source": getattr(getattr(r, "source", None), "name", ""),
                    "destination": getattr(getattr(r, "destination", None), "name", ""),
                    "description": getattr(r, "description", ""),
                    "technology": getattr(r, "technology", ""),
                }
            )
        except Exception:
            continue

    return json.dumps(data, indent=2, sort_keys=True)


# Register exporters
register_exporter("structurizr", structurizr_dump)
register_exporter("json", _as_json_graph)
