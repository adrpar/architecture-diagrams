from __future__ import annotations

from typing import List

from architecture_diagrams.c4.model import ViewType
from architecture_diagrams.orchestrator.specs import ExcludeRelByName, IncludeRelByName, ViewSpec


def get_views() -> List[ViewSpec]:
    return [
        ViewSpec(
            key="PortalContext",
            name="Customer Portal Context",
            view_type=ViewType.SYSTEM_CONTEXT,
            description="Context view for Customer Portal",
            subject="Customer Portal",
            includes=["Customer Portal", "Identity Provider", "Payments"],
            filters=[
                # Show only auth and payment relationships
                IncludeRelByName(
                    from_name="Customer Portal/Web App", to_name="Identity Provider/Auth Server"
                ),
                IncludeRelByName(
                    from_name="Customer Portal/Web App", to_name="Payments/Payments API"
                ),
            ],
        ),
        ViewSpec(
            key="MobileContainer",
            name="Mobile Banking Container",
            view_type=ViewType.CONTAINER,
            description="Container view for Mobile Banking",
            subject="Mobile Banking/Web App",
            includes=["Mobile Banking", "Payments", "Identity Provider"],
            filters=[
                ExcludeRelByName(
                    from_name="*",
                    to_name="*",
                    but_include_names=[
                        "Identity Provider/Auth Server",
                        "Payments/Payments API",
                    ],
                )
            ],
        ),
    ]
