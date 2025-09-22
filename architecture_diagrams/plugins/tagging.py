from __future__ import annotations

from typing import Callable, Dict, Optional

Strategy = Callable[[object], None]

_taggers: Dict[str, Strategy] = {}


def register_strategy(name: str, fn: Strategy) -> None:
    _taggers[name.strip().lower()] = fn


def get_strategy(name: str) -> Optional[Strategy]:
    return _taggers.get(name.strip().lower())


def list_strategies() -> list[str]:
    return sorted(_taggers.keys())


# --- Default strategies ---
def _noop(_: object) -> None:  # no-op tagging
    return None


def _auto_external(model: object) -> None:
    """Best-effort: tag clearly external software systems as 'external'.

    Heuristics (conservative):
      - Description contains the word 'External' (case-insensitive)
      - Name contains common 3rd-party terms (e.g., 'Provider', 'Gateway', 'Clearing')
    """

    def _norm(s: Optional[str]) -> str:
        return (s or "").lower()

    systems = getattr(model, "software_systems", {})
    for sys in systems.values():
        name = _norm(getattr(sys, "name", ""))
        desc = _norm(getattr(sys, "description", ""))
        if "external" in desc or any(k in name for k in ("provider", "gateway", "clearing")):
            raw = getattr(sys, "tags", None)
            items = []
            if isinstance(raw, set):
                items = list(raw)
            elif isinstance(raw, (list, tuple)):
                items = list(raw)
            new_tags = {str(x) for x in items}
            new_tags.add("external")
            sys.tags = new_tags  # type: ignore[attr-defined]


def _auto_broker_queue(model: object) -> None:
    """Tag containers as message-broker/queue based on technology/name heuristics.

    - If container.technology contains 'kafka' -> add 'message-broker'
    - If name or technology contains 'redis stream' or 'queue' -> add 'message-broker' and 'queue'
    """
    def _norm(s: Optional[str]) -> str:
        return (s or "").lower()

    systems = getattr(model, "software_systems", {})
    for sys in systems.values():
        for c in getattr(sys, "containers", []):
            name = _norm(getattr(c, "name", ""))
            tech = _norm(getattr(c, "technology", ""))
            tags = set(getattr(c, "tags", set()) or set())
            if "kafka" in tech or "kafka" in name:
                tags.add("message-broker")
            if "redis stream" in tech or "redis streams" in tech or "queue" in name or "queue" in tech:
                tags.add("message-broker")
                tags.add("queue")
            try:
                c.tags = tags  # type: ignore[attr-defined]
            except Exception:
                pass


# Register built-ins
register_strategy("none", _noop)
register_strategy("auto_external", _auto_external)
register_strategy("auto_broker_queue", _auto_broker_queue)
