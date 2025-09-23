"""Generic two-phase registration helpers (moved from diag package).

Provides convention-based wrappers to remove per-module boilerplate `register_*` functions.

Convention:
    For a system module named `<name>_c4.py` located in `architecture_diagrams.diag`, if it defines
    - `define_<name>(model)` and `link_<name>(model)` functions
  you can call::

    from architecture_diagrams.c4.auto_two_phase import auto_register
    auto_register(model, "payments_core")  # resolves to define_payments_core + link_payments_core

  Or build multiple at once::

    auto_register_all(model, ["payments_core", "identity", "channels"])

Phases:
  phase="define" runs only the define function.
  phase="link"   runs only the link function (raises if define has not run and system absent).
  phase="all"    (default) runs define then link.

Additional convention variable (optional) in each module:
    SYSTEM_KEY = "payments-core"   # canonical system name if it differs from file stem
If absent, we infer system key by replacing underscores in <name> with hyphens.

This lets us delete explicit register_* boilerplate across modules.
"""

from __future__ import annotations

from enum import Enum
from importlib import import_module
from types import ModuleType
from typing import List, Optional, Sequence, Union

from . import SoftwareSystem, SystemLandscape


class Phase(
    str, Enum
):  # str subclass so existing string comparisons still work if any external code inspects value
    DEFINE = "define"
    LINK = "link"
    ALL = "all"

    @classmethod
    def coerce(cls, value: Union["Phase", str]) -> "Phase":
        if isinstance(value, Phase):
            return value
        try:
            return cls(value)  # type: ignore[arg-type]
        except ValueError as e:  # pragma: no cover - defensive
            raise ValueError("phase must be one of {'define','link','all'}") from e


def _infer_system_key(module: ModuleType, name: str) -> str:
    return getattr(module, "SYSTEM_KEY", name.replace("_", "-"))


def _import_c4_module(name: str, project: Optional[str] = None) -> ModuleType:
    """Import a C4 module by name from projects/<project>/models.

    Only the explicit project is supported; there is no fallback to any other project.
    """
    if not project:
        raise ModuleNotFoundError(
            "Project must be specified to import C4 module (e.g., projects.<project>.models.<name>_c4)"
        )
    mod_name = f"projects.{project}.models.{name}_c4"
    return import_module(mod_name)


def auto_register(
    model: SystemLandscape,
    name: str,
    phase: Union[Phase, str] = Phase.ALL,
    *,
    project: Optional[str] = None,
) -> SoftwareSystem | dict[str, SoftwareSystem]:
    """Auto-register a C4 system module.

    phase may be a Phase enum member or one of the strings: 'define', 'link', 'all'.
    """
    phase_enum = Phase.coerce(phase)

    # If no explicit project provided, infer from model.name to support projects/<project>/ layout transparently
    effective_project = project or getattr(model, "name", None)
    module = _import_c4_module(name, project=effective_project)

    define_function_name = f"define_{name}"
    link_function_name = f"link_{name}"
    if not hasattr(module, define_function_name):
        raise AttributeError(f"Module {module.__name__} missing {define_function_name}")

    link_function = getattr(module, link_function_name, None)
    define_function = getattr(module, define_function_name)

    system_key = _infer_system_key(module, name)

    defined = None
    if phase_enum in {Phase.DEFINE, Phase.ALL}:
        defined = define_function(model)
    if phase_enum in {Phase.LINK, Phase.ALL} and link_function is not None:
        if defined is None:
            existing = next(
                (s for s in model.software_systems.values() if s.name == system_key), None
            )
            if existing is None:
                raise ValueError(f"Cannot link {system_key} before it is defined")
            defined = existing
        link_function(model)
    if defined is None:
        raise RuntimeError("auto_register produced no system; check module functions")
    return defined


def auto_register_all(
    model: SystemLandscape,
    names: Sequence[str],
    phase: Union[Phase, str] = Phase.ALL,
    *,
    project: Optional[str] = None,
) -> List[SoftwareSystem | dict[str, SoftwareSystem]]:
    results: List[SoftwareSystem | dict[str, SoftwareSystem]] = []
    for n in names:
        results.append(auto_register(model, n, phase=phase, project=project))
    return results


__all__ = ["auto_register", "auto_register_all", "Phase"]
