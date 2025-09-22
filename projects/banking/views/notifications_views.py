from __future__ import annotations
from typing import List

from architecture_diagrams.c4.model import ViewType
from architecture_diagrams.orchestrator.specs import ViewSpec, ExcludeRelByName


def get_views() -> List[ViewSpec]:
    return [
        ViewSpec(
            key="NotificationsContainer",
            name="Notifications Container",
            view_type=ViewType.CONTAINER,
            description="Container view focused on Notifications",
            subject="Notifications/Event Router",
            includes=[
                "Notifications/Event Router",
                "Notifications/Email Service",
                "Notifications/SMS Service",
                "Payments/Payments API",
                "Core Banking/Ledger Service",
                "Email Provider/SMTP",
                "SMS Gateway/SMPP",
            ],
            # Demonstrate exclude with but-include cross references
            filters=[
                ExcludeRelByName(from_name="*", to_name="*", but_include_names=[
                    "Payments/Payments API",
                    "Email Provider/SMTP",
                    "SMS Gateway/SMPP",
                ])
            ],
        ),
    ]
