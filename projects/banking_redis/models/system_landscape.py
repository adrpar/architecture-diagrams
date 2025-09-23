from __future__ import annotations

from typing import Optional

from architecture_diagrams.c4.system_landscape import SystemLandscape


def build(model: Optional[SystemLandscape] = None) -> SystemLandscape:
    """Variant builder that reuses base banking and applies an overlay.

    Steps:
    - Build the base 'banking' model by invoking its builder
    - Replace Eventing/Kafka container with Eventing/Redis Queue
    - Rewire relationships from/to Kafka accordingly
    """
    # 1) Build base banking model
    from projects.banking.models.system_landscape import build as base_build

    model = base_build(model)

    # Overlays (apply functions) will run after compose; nothing else needed here.
    return model
