from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TypedDict

from architecture_diagrams.c4.model import ViewType
from architecture_diagrams.orchestrator.specs import IncludeRelByName, ViewSpec

# View generator signature: (model, config) -> list[ViewSpec]
GeneratorFn = Callable[[object, Dict[str, Any]], List[ViewSpec]]


@dataclass(frozen=True)
class _VGRegistry:
    generators: Dict[str, GeneratorFn]


_reg = _VGRegistry(generators={})


def register_view_generator(name: str, fn: GeneratorFn) -> None:
    _reg.generators[name.strip().lower()] = fn


def get_view_generator(name: str) -> Optional[GeneratorFn]:
    return _reg.generators.get(name.strip().lower())


def list_view_generators() -> list[str]:
    return sorted(_reg.generators.keys())


class _DeltaCfg(TypedDict, total=False):
    name: str
    title: str
    description: str
    before: Dict[str, str]
    after: Dict[str, str]
    include_systems: List[str]
    view_type: str


# --- Built-in: lineage/delta generator ---
def _delta_lineage(model: object, cfg: Dict[str, Any]) -> List[ViewSpec]:
    """Create lineage/delta views given a before/after container config.

    Config shape (all strings unless stated):
      name: Required unique key suffix, e.g., "EventingDeltaKafkaToRedis"
      title: Optional display name; defaults to name
      description: Optional
      before: { system: "Eventing", container: "Kafka" }
      after:  { system: "Eventing", container: "Redis Queue" }
      include_systems: Optional[List[str]] additional systems to include
      view_type: Optional["SystemLandscape"|"Container"] (default SystemLandscape)

    Output: Two views: a combined delta view and an "after" focused view.
    """
    name = str(cfg.get("name") or "DeltaView").strip()
    title = str(cfg.get("title") or name)
    desc = str(cfg.get("description") or "")
    before: Dict[str, Any] = dict(cfg.get("before") or {})
    after: Dict[str, Any] = dict(cfg.get("after") or {})
    b_sys = str(before.get("system") or "").strip()
    b_cont = str(before.get("container") or "").strip()
    a_sys = str(after.get("system") or "").strip()
    a_cont = str(after.get("container") or "").strip()
    include_systems: List[str] = list(cfg.get("include_systems") or [])
    vt = str(cfg.get("view_type") or ViewType.SYSTEM_LANDSCAPE)

    # Build name-based relationship includes for before/after adjacency
    rel_filters: List[IncludeRelByName] = []
    if b_cont:
        rel_filters.append(IncludeRelByName(from_name="*", to_name=f"{b_sys}/{b_cont}"))
        rel_filters.append(IncludeRelByName(from_name=f"{b_sys}/{b_cont}", to_name="*"))
    if a_cont:
        rel_filters.append(IncludeRelByName(from_name="*", to_name=f"{a_sys}/{a_cont}"))
        rel_filters.append(IncludeRelByName(from_name=f"{a_sys}/{a_cont}", to_name="*"))

    includes: List[str] = []
    # Always include the systems containing the before/after containers
    for s in (b_sys, a_sys):
        if s and s not in includes:
            includes.append(s)
    for s in include_systems:
        if s not in includes:
            includes.append(s)

    combined = ViewSpec(
        key=name,
        name=title,
        view_type=vt,
        description=desc or f"Delta: {b_cont} -> {a_cont}",
        includes=includes,
        filters=rel_filters,
        smart=True if vt == ViewType.SYSTEM_LANDSCAPE else False,
    )

    after_only = ViewSpec(
        key=f"{name}After",
        name=f"{title} (After)",
        view_type=vt,
        description=f"After: {a_cont}",
        includes=includes,
        filters=[
            (
                IncludeRelByName(from_name="*", to_name=f"{a_sys}/{a_cont}")
                if a_cont
                else IncludeRelByName()
            ),
            (
                IncludeRelByName(from_name=f"{a_sys}/{a_cont}", to_name="*")
                if a_cont
                else IncludeRelByName()
            ),
        ],
        smart=True if vt == ViewType.SYSTEM_LANDSCAPE else False,
    )

    return [combined, after_only]


# Register built-in
register_view_generator("delta_lineage", _delta_lineage)
