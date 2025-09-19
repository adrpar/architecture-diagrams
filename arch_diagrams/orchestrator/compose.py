from __future__ import annotations
from typing import Iterable, Optional, Callable

from arch_diagrams.c4.system_landscape import SystemLandscape


ModelBuilder = Callable[[Optional[SystemLandscape]], SystemLandscape]


def compose(models: Iterable[ModelBuilder], *, name: str = "banking") -> SystemLandscape:
    """Compose multiple model builder callables into a single SystemLandscape.

    Each callable should accept an optional SystemLandscape and return a SystemLandscape.
    """
    model: Optional[SystemLandscape] = SystemLandscape(name=name)
    for builder in models:
        model = builder(model)
    assert model is not None
    return model
