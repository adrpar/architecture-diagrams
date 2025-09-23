from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Optional

# Exporter is a callable that takes a model and returns a string representation
Exporter = Callable[[object], str]


@dataclass(frozen=True)
class PluginRegistry:
    exporters: Dict[str, Exporter]

    @classmethod
    def default(cls) -> "PluginRegistry":
        return cls(exporters={})


_registry: PluginRegistry = PluginRegistry.default()


def register_exporter(name: str, fn: Exporter) -> None:
    key = name.strip().lower()
    _registry.exporters[key] = fn


def get_exporter(name: str) -> Optional[Exporter]:
    return _registry.exporters.get(name.strip().lower())


def list_exporters() -> list[str]:
    return sorted(_registry.exporters.keys())
