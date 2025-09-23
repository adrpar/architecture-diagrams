from __future__ import annotations

from typing import Iterable, List, Optional, Set

from architecture_diagrams.orchestrator.specs import ViewSpec


def select_views(
    views: Iterable[ViewSpec],
    *,
    names: Optional[Set[str]] = None,
    tags: Optional[Set[str]] = None,
    modules: Optional[Set[str]] = None,
) -> List[ViewSpec]:
    names = names or set()
    tags = tags or set()
    modules = _normalize_set(modules or set())

    if not names and not tags and not modules:
        return list(views)

    selected: List[ViewSpec] = []

    for v in views:
        # Select by explicit name/key
        if v.key in names or v.name in names:
            selected.append(v)
            continue
        # Select by tags
        if tags and (v.tags & tags):
            selected.append(v)
            continue
        # Select by module (derived from subject root, e.g., "connect" from "connect/bff")
        if modules:
            mod = _subject_root(v.subject)
            if mod and _norm(mod) in modules:
                selected.append(v)
                continue

    return selected


def _norm(s: str) -> str:
    return s.strip().lower().replace("_", "-").replace(" ", "-")


def _normalize_set(values: Set[str]) -> Set[str]:
    return {_norm(v) for v in values}


def _subject_root(subject: Optional[str]) -> Optional[str]:
    if not subject:
        return None
    return subject.split("/", 1)[0]
