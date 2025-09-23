from __future__ import annotations

from typing import List

from architecture_diagrams.c4.model import ViewType
from architecture_diagrams.orchestrator.specs import ExcludeRelByName, IncludeRelByName, ViewSpec


def get_views() -> List[ViewSpec]:
    return [
        ViewSpec(
            key="EventingRedisOverview",
            name="Eventing with Redis Queue",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="Event-driven backbone connecting producers and consumers via Redis Queue",
            includes=[
                "Eventing/Redis Queue",
                "Notifications/Event Router",
                # Removed Reporting/ETL Job to differentiate this view from the inherited one
                # "Reporting/ETL Job",
                "Core Banking/Ledger Service",
                "Payments/Payments API",
            ],
            smart=True,
            filters=[
                IncludeRelByName(
                    from_name="Core Banking/Ledger Service", to_name="Eventing/Redis Queue"
                ),
                IncludeRelByName(from_name="Payments/Payments API", to_name="Eventing/Redis Queue"),
                IncludeRelByName(
                    from_name="Eventing/Redis Queue", to_name="Notifications/Event Router"
                ),
                # Removed Redis -> ETL to keep this view focused on routing to notifications
                # IncludeRelByName(from_name="Eventing/Redis Queue", to_name="Reporting/ETL Job"),
            ],
        ),
        ViewSpec(
            key="EventingDeltaKafkaToRedis",
            name="Delta: Kafka -> Redis",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="Highlight change from Kafka to Redis Queue (Kafka retained; Kafka edges hidden)",
            includes=[
                # Include both Kafka and Redis so the node appears with deprecated tag
                "Eventing/Kafka",
                "Eventing/Redis Queue",
                "Notifications/Event Router",
                "Reporting/ETL Job",
                "Payments/Payments API",
                "Core Banking/Ledger Service",
            ],
            smart=True,
            excludes=[
                # Do not exclude Kafka element; we only exclude its edges via name-based filters below
            ],
            filters=[
                # Remove all Kafka edges while keeping the node present
                ExcludeRelByName(from_name="*", to_name="Eventing/Kafka"),
                ExcludeRelByName(from_name="Eventing/Kafka", to_name="*"),
                # Keep Redis edges visible
                IncludeRelByName(
                    from_name="Core Banking/Ledger Service", to_name="Eventing/Redis Queue"
                ),
                IncludeRelByName(from_name="Payments/Payments API", to_name="Eventing/Redis Queue"),
                IncludeRelByName(
                    from_name="Eventing/Redis Queue", to_name="Notifications/Event Router"
                ),
                IncludeRelByName(from_name="Eventing/Redis Queue", to_name="Reporting/ETL Job"),
            ],
        ),
    ]
