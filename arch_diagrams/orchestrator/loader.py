from __future__ import annotations
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec
import sys
from pathlib import Path
from typing import List, Optional

from arch_diagrams.orchestrator.compose import ModelBuilder
from arch_diagrams.orchestrator.specs import ViewSpec


def discover_model_builders(root: Path, project: Optional[str] = None) -> List[ModelBuilder]:
    """Discover model builders from root-level projects only.

    Supported layout (enforced):
      - projects/<project>/models/**/system_landscape.py

    Each module must export a callable "build(model: Optional[SystemLandscape]) -> SystemLandscape".
    """
    results: List[ModelBuilder] = []
    searched: List[Path] = []

    if project:
        pref_root = root / "projects" / project / "models"
        if pref_root.exists():
            searched.append(pref_root)

    for base_dir in searched:
        for path in base_dir.rglob("system_landscape.py"):
            rel = path.relative_to(root).with_suffix("")
            mod_name = ".".join(rel.parts)
            try:
                mod = import_module(mod_name)
            except Exception:
                spec = spec_from_file_location(mod_name, path)
                if spec is None or spec.loader is None:
                    continue
                mod = module_from_spec(spec)
                sys.modules[mod_name] = mod
                spec.loader.exec_module(mod)
            if hasattr(mod, "build"):
                results.append(getattr(mod, "build"))
    return results


def discover_view_specs(root: Path, project: Optional[str] = None) -> List[ViewSpec]:
    """Discover view specs (modules exporting get_views()) from root-level projects only.

    Supported layout (enforced):
      - projects/<project>/views/**/*.py
    """
    results: List[ViewSpec] = []
    searched: List[Path] = []
    if project:
        pref_root = root / "projects" / project / "views"
        if pref_root.exists():
            searched.append(pref_root)
    # No global or in-package discovery supported anymore

    for base_dir in searched:
        for path in base_dir.rglob("*.py"):
            if path.name.startswith("_"):
                continue
            rel = path.relative_to(root).with_suffix("")
            mod_name = ".".join(rel.parts)
            try:
                mod = import_module(mod_name)
            except Exception:
                spec = spec_from_file_location(mod_name, path)
                if spec is None or spec.loader is None:
                    continue
                mod = module_from_spec(spec)
                sys.modules[mod_name] = mod
                spec.loader.exec_module(mod)
            if hasattr(mod, "get_views"):
                views = getattr(mod, "get_views")()
                results.extend(views)
    return results
