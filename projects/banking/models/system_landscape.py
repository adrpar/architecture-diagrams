from __future__ import annotations
from typing import Optional
from pathlib import Path

from arch_diagrams.c4.system_landscape import SystemLandscape
from arch_diagrams.c4.auto_two_phase import auto_register


def build(model: Optional[SystemLandscape] = None) -> SystemLandscape:
    """Entry point builder for the BANKING project (projects/banking).

    Discovers local `*_c4.py` under projects/banking/models and auto-registers them.
    """
    model = model or SystemLandscape(name="banking")
    local_dir = Path(__file__).resolve().parent

    def scan_names(dir_path: Path) -> set[str]:
        names: set[str] = set()
        if dir_path.exists():
            for p in dir_path.glob("*_c4.py"):
                stem = p.stem
                if stem.endswith("_c4"):
                    names.add(stem[:-3])
        return names

    discovered = scan_names(local_dir)
    module_names = sorted(discovered)
    # First define all modules to ensure systems exist regardless of file ordering
    for name in module_names:
        auto_register(model, name, phase="define", project="banking")
    # Then link relationships
    for name in module_names:
        auto_register(model, name, phase="link", project="banking")
    return model
