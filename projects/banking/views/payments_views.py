from __future__ import annotations

from typing import List

from architecture_diagrams.c4 import ViewType
from architecture_diagrams.orchestrator.specs import ViewSpec


def get_views() -> List[ViewSpec]:
    return [
        ViewSpec(
            key="PaymentsContainer",
            name="Payments Container",
            view_type=ViewType.CONTAINER,
            description="Container view for Payments",
            subject="Payments/Payments API",
            includes=["Payments", "Core Banking"],
        ),
        ViewSpec(
            key="CoreComponent",
            name="Core Banking Component",
            view_type=ViewType.COMPONENT,
            description="Component view for Core Banking Accounts Service",
            subject="Core Banking/Accounts Service",
            includes=["Core Banking/Accounts Service", "Payments/Payments API"],
        ),
    ]
