from __future__ import annotations
from typing import List

from architecture_diagrams.c4.model import ViewType
from architecture_diagrams.orchestrator.specs import ViewSpec, IncludeRelByName


def get_views() -> List[ViewSpec]:
    return [
        ViewSpec(
            key="ReportingDataLineage",
            name="Reporting Data Lineage",
            view_type=ViewType.CONTAINER,
            description="Lineage of data extracted by ETL",
            subject="Reporting/ETL Job",
            includes=[
                "Reporting/ETL Job",
                "Core Banking/Accounts Service",
                "Payments/Payments API",
                "Reporting/BI Tool",
            ],
            filters=[
                IncludeRelByName(from_name="Reporting/ETL Job", to_name="Core Banking/Accounts Service"),
                IncludeRelByName(from_name="Reporting/ETL Job", to_name="Payments/Payments API"),
            ],
        ),
    ]
