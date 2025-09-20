from __future__ import annotations
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec
import sys
from pathlib import Path
from typing import List, Optional

from arch_diagrams.orchestrator.compose import ModelBuilder
from arch_diagrams.orchestrator.specs import ViewSpec


## Legacy alias mapping ('arch_diags' -> 'arch_diagrams') was removed.
## External projects must import 'arch_diagrams' directly.

def _ensure_projects_parent_on_syspath(paths: List[Path]) -> None:
    """Add the parent of any discovered 'projects' directory to sys.path for external imports.

    This allows external modules to `import projects.<name>....` successfully.
    """
    try:
        for p in paths:
            cur = p.resolve()
            # Walk up to find a 'projects' directory in the ancestors
            while cur.name != 'projects' and cur.parent != cur:
                cur = cur.parent
            if cur.name == 'projects':
                top = cur.parent
                import sys as _sys
                if str(top) not in _sys.path:
                    _sys.path.insert(0, str(top))
    except Exception:
        pass

def preload_external_project_packages(paths: List[Path]) -> None:
    """Eagerly import external 'projects.<name>' packages for given model/view directories.

    This avoids conflicts when an internal 'projects' package is already imported,
    by explicitly creating sys.modules entries for 'projects.<name>'.
    """
    import sys as _sys
    try:
        for p in paths:
            cur = p.resolve()
            # Expect .../projects/<name>/(models|views)
            parent = cur.parent
            if parent.name in ("models", "views"):
                proj_dir = parent.parent
            else:
                proj_dir = parent
            if proj_dir.parent.name != 'projects':
                continue
            init_py = proj_dir / "__init__.py"
            if not init_py.exists():
                continue
            mod_name = f"projects.{proj_dir.name}"
            if mod_name in _sys.modules:
                continue
            spec = spec_from_file_location(mod_name, init_py)
            if spec is None or spec.loader is None:
                continue
            mod = module_from_spec(spec)
            _sys.modules[mod_name] = mod
            spec.loader.exec_module(mod)
    except Exception:
        # Best-effort only
        pass


def discover_model_builders(root: Path, project: Optional[str] = None, extra_dirs: Optional[List[Path]] = None) -> List[ModelBuilder]:
    """Discover model builders from root-level projects only.

    Supported layout (enforced):
      - projects/<project>/models/**/system_landscape.py

    Each module must export a callable "build(model: Optional[SystemLandscape]) -> SystemLandscape".
    """
    results: List[ModelBuilder] = []
    searched: List[Path] = []
    if extra_dirs:
        _ensure_projects_parent_on_syspath(extra_dirs)
        preload_external_project_packages(extra_dirs)

    if project:
        pref_root = root / "projects" / project / "models"
        if pref_root.exists():
            searched.append(pref_root)
    # Support external project directories passed by build: allow direct models/ under provided root
    if extra_dirs:
        for d in extra_dirs:
            if d.exists():
                searched.append(d)

    for base_dir in searched:
        for path in base_dir.rglob("system_landscape.py"):
            # Derive a module name; prefer repo-relative when possible, otherwise synthesize a unique name
            try:
                rel = path.relative_to(root).with_suffix("")
                mod_name = ".".join(rel.parts)
            except Exception:
                mod_name = "external_" + "_".join(path.with_suffix("").parts[-6:])
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


def discover_view_specs(root: Path, project: Optional[str] = None, extra_dirs: Optional[List[Path]] = None) -> List[ViewSpec]:
    """Discover view specs (modules exporting get_views()) from root-level projects only.

    Supported layout (enforced):
      - projects/<project>/views/**/*.py
    """
    results: List[ViewSpec] = []
    searched: List[Path] = []
    if extra_dirs:
        _ensure_projects_parent_on_syspath(extra_dirs)
        preload_external_project_packages(extra_dirs)
    if project:
        pref_root = root / "projects" / project / "views"
        if pref_root.exists():
            searched.append(pref_root)
    # Support external project directories passed by build: allow direct views/ under provided root
    if extra_dirs:
        for d in extra_dirs:
            if d.exists():
                searched.append(d)

    for base_dir in searched:
        project_label = base_dir.parent.name
        for path in base_dir.rglob("*.py"):
            if path.name.startswith("_"):
                continue
            try:
                rel = path.relative_to(root).with_suffix("")
                mod_name = ".".join(rel.parts)
            except Exception:
                mod_name = "external_" + "_".join(path.with_suffix("").parts[-6:])
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
                # Annotate each view with the originating project label
                for v in views:
                    try:
                        setattr(v, "project", project_label)
                    except Exception:
                        pass
                results.extend(views)
    return results
