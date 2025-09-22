from __future__ import annotations
from typing import List

from architecture_diagrams.c4.model import ViewType
from architecture_diagrams.orchestrator.specs import ViewSpec, IncludeRelByName


def get_views() -> List[ViewSpec]:
    # Container-level view to spotlight Eventing's Kafka edges in the base project
    return [
        ViewSpec(
            key="EventingContainerChange",
            name="Eventing Container Change",
            view_type=ViewType.CONTAINER,
            description="Container-level view of Eventing highlighting Kafka connectivity",
            subject="Eventing/Kafka",
            includes=[
                "Eventing/Kafka",
                "Notifications/Event Router",
                "Reporting/ETL Job",
                "Core Banking/Ledger Service",
                "Payments/Payments API",
            ],
            # Restrict to only the relationships that represent the backbone through Kafka
            filters=[
                IncludeRelByName(from_name="Core Banking/Ledger Service", to_name="Eventing/Kafka"),
                IncludeRelByName(from_name="Payments/Payments API", to_name="Eventing/Kafka"),
                IncludeRelByName(from_name="Eventing/Kafka", to_name="Notifications/Event Router"),
                IncludeRelByName(from_name="Eventing/Kafka", to_name="Reporting/ETL Job"),
            ],
            smart=False,
        ),
    ]
