from __future__ import annotations
from typing import List

from architecture_diagrams.c4.model import ViewType
from architecture_diagrams.orchestrator.specs import ViewSpec, IncludeRelByName, derive_view


def get_views() -> List[ViewSpec]:
    # Derived container-level view focusing on Redis Queue (proposed)
    return [
        derive_view(
            base_key="EventingContainerChange",
            key="EventingContainerChangeRedis",
            name="Eventing Container Change (Redis)",
            view_type=ViewType.CONTAINER,
            description="Container-level view highlighting Redis Queue replacing Kafka",
            subject="Eventing/Redis Queue",
            includes=[
                "Eventing/Redis Queue",
                "Notifications/Event Router",
                "Reporting/ETL Job",
                "Core Banking/Ledger Service",
                "Payments/Payments API",
            ],
            filters=[
                IncludeRelByName(from_name="Core Banking/Ledger Service", to_name="Eventing/Redis Queue"),
                IncludeRelByName(from_name="Payments/Payments API", to_name="Eventing/Redis Queue"),
                IncludeRelByName(from_name="Eventing/Redis Queue", to_name="Notifications/Event Router"),
                IncludeRelByName(from_name="Eventing/Redis Queue", to_name="Reporting/ETL Job"),
            ],
            smart=False,
        ),
    ]
