from __future__ import annotations

from architecture_diagrams.orchestrator.specs import ViewSpec


def get_views() -> list[ViewSpec]:
    """Showcase of config-driven delta_lineage view generation.

    This file defines a minimal base view and relies on the CLI's --view-generator and
    --view-generator-config to produce derived delta views at build time. Keeping this
    here demonstrates where teams can drop simple base views/configs.
    """
    # Provide a small anchor view to ensure systems appear in basic selection
    return [
        ViewSpec(
            key="EventingAnchor",
            name="Eventing Anchor",
            view_type="SystemLandscape",
            description="Anchor view for Eventing delta generation",
            includes=["Eventing", "Core Banking", "Payments"],
            smart=True,
        )
    ]
