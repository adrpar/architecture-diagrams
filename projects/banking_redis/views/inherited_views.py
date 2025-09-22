from __future__ import annotations
from typing import List

from architecture_diagrams.c4.model import ViewType
from architecture_diagrams.orchestrator.specs import ViewSpec, IncludeRelByName, derive_view


def get_views() -> List[ViewSpec]:
    return [
        # Extend the base EventingOverview to switch to Redis elements and add an extra include
        derive_view(
            base_key="EventingOverview",
            key="EventingOverviewRedisInherited",
            name="Eventing Overview (Redis, inherited)",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            includes=[
                "Eventing/Redis Queue",  # add Redis explicitly
            ],
            # Adjust filters to include Redis edges
            filters=[
                IncludeRelByName(from_name="Core Banking/Ledger Service", to_name="Eventing/Redis Queue"),
                IncludeRelByName(from_name="Payments/Payments API", to_name="Eventing/Redis Queue"),
                IncludeRelByName(from_name="Eventing/Redis Queue", to_name="Notifications/Event Router"),
                IncludeRelByName(from_name="Eventing/Redis Queue", to_name="Reporting/ETL Job"),
            ],
            smart=True,
        ),
    ]
