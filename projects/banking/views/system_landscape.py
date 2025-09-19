from __future__ import annotations
from typing import List

from arch_diagrams.c4.model import ViewType
from arch_diagrams.orchestrator.specs import ViewSpec, IncludeRelByName, ExcludeRelByName


def get_views() -> List[ViewSpec]:
    return [
        ViewSpec(
            key="TotalBankingSystemsOverview",
            name="Whole Banking systems overview",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="All banking systems and external partners",
            includes=[ ],
            smart=True,
        ),
        ViewSpec(
            key="BankingSystemsOverview",
            name="Banking systems overview",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="Core banking systems and external partners",
            includes=[
                "Core Banking",
                "Payments",
                "Customer Portal",
                "Mobile Banking",
                "Identity Provider",
                "Notifications",
                "Reporting",
                "Clearing House",
            ],
            smart=True,
        ),
        ViewSpec(
            key="ChannelsAccessXref",
            name="Channels Access XRef",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="Customer channels accessing Identity and Payments",
            includes=[
                "Customer Portal",
                "Mobile Banking",
                "Identity Provider/Auth Server",
                "Payments/Payments API",
            ],
            smart=True,
            filters=[
                IncludeRelByName(from_name="Customer Portal/Web App", to_name="Identity Provider/Auth Server"),
                IncludeRelByName(from_name="Customer Portal/Web App", to_name="Payments/Payments API"),
                IncludeRelByName(from_name="Mobile Banking/iOS App", to_name="Identity Provider/Auth Server"),
                IncludeRelByName(from_name="Mobile Banking/iOS App", to_name="Payments/Payments API"),
                IncludeRelByName(from_name="Mobile Banking/Android App", to_name="Identity Provider/Auth Server"),
                IncludeRelByName(from_name="Mobile Banking/Android App", to_name="Payments/Payments API"),
            ],
        ),
        ViewSpec(
            key="FraudRiskXref",
            name="Fraud & Risk XRef",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="Fraud scoring crossing Payments and Risk & ML, plus lineage to Reporting",
            includes=[
                "Payments/Payments API",
                "Payments/Fraud Service",
                "Risk & ML/Model Serving",
                "Risk & ML/Feature Store",
                "Reporting/ETL Job",
            ],
            smart=True,
            filters=[
                IncludeRelByName(from_name="Payments/Fraud Service", to_name="Risk & ML/Model Serving"),
                IncludeRelByName(from_name="Payments/Fraud Service", to_name="Payments/Payments API"),
                IncludeRelByName(from_name="Risk & ML/Feature Store", to_name="Risk & ML/Model Serving"),
                IncludeRelByName(from_name="Risk & ML/Training Pipeline", to_name="Reporting/ETL Job"),
            ],
        ),
        ViewSpec(
            key="ClearingXref",
            name="Clearing XRef",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="Clearing adapter interactions with external clearing house",
            includes=[
                "Payments/Clearing Adapter",
                "Clearing House/Clearing API",
                "Payments/Payments API",
            ],
            smart=True,
            filters=[
                IncludeRelByName(from_name="Payments/Clearing Adapter", to_name="Clearing House/Clearing API"),
                IncludeRelByName(from_name="Payments/Clearing Adapter", to_name="Payments/Payments API"),
            ],
        ),
        ViewSpec(
            key="EventingFocusedXref",
            name="Eventing-focused XRef",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="Show only the intended in/out edges of Kafka (Eventing) with nearby producers/consumers",
            includes=[
                "Eventing/Kafka",
                "Notifications/Event Router",
                "Reporting/ETL Job",
                "Payments/Payments API",
                "Core Banking/Ledger Service",
            ],
            smart=True,
            filters=[
                # Exclude all outgoing from Kafka except to Event Router and ETL Job
                ExcludeRelByName(from_name="Eventing/Kafka", to_name="*", but_include_names=[
                    "Notifications/Event Router",
                    "Reporting/ETL Job",
                ]),
                # Exclude all incoming to Kafka except from Ledger and Payments API
                ExcludeRelByName(from_name="*", to_name="Eventing/Kafka", but_include_names=[
                    "Core Banking/Ledger Service",
                    "Payments/Payments API",
                ]),
            ],
        ),
        ViewSpec(
            key="OpenBankingMinimalXref",
            name="Open Banking minimal XRef",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="API Gateway edges restricted to consent, identity, and accounts only",
            includes=[
                "Open Banking/API Gateway",
                "Open Banking/Consent Service",
                "Identity Provider/Auth Server",
                "Core Banking/Accounts Service",
            ],
            smart=True,
            filters=[
                # Exclude all outgoing from API Gateway except the three key destinations
                ExcludeRelByName(from_name="Open Banking/API Gateway", to_name="*", but_include_names=[
                    "Identity Provider/Auth Server",
                    "Open Banking/Consent Service",
                    "Core Banking/Accounts Service",
                ]),
                # Optionally, block any other incoming edges into Accounts except API Gateway
                ExcludeRelByName(from_name="*", to_name="Core Banking/Accounts Service", but_include_names=[
                    "Open Banking/API Gateway",
                ]),
            ],
        ),
        ViewSpec(
            key="BankingDataFlows",
            name="Banking Data Flows",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="Highlight ETL and event-driven flows across systems",
            includes=[
                "Reporting",
                "Core Banking/Accounts Service",
                "Payments/Payments API",
                "Notifications/Event Router",
            ],
            smart=True,
            # Relationship name-based filters: include only specific directions
            filters=[
                IncludeRelByName(from_name="Reporting/ETL Job", to_name="Core Banking/Accounts Service"),
                IncludeRelByName(from_name="Reporting/ETL Job", to_name="Payments/Payments API"),
                IncludeRelByName(from_name="Payments/Payments API", to_name="Notifications/Event Router"),
                IncludeRelByName(from_name="Core Banking/Ledger Service", to_name="Notifications/Event Router"),
            ],
        ),
        ViewSpec(
            key="AmlScreeningFlow",
            name="AML & Sanctions Screening",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="Show KYC/AML checks during account creation and sanctions screening on payments",
            includes=[
                "Core Banking/Accounts Service",
                "Payments/Payments API",
                "Compliance/KYC Service",
                "Compliance/Sanctions Screening",
                "Compliance/Case Manager",
            ],
            smart=True,
            filters=[
                IncludeRelByName(from_name="Core Banking/Accounts Service", to_name="Compliance/KYC Service"),
                IncludeRelByName(from_name="Payments/Payments API", to_name="Compliance/Sanctions Screening"),
                IncludeRelByName(from_name="Compliance/KYC Service", to_name="Compliance/Case Manager"),
                IncludeRelByName(from_name="Compliance/Sanctions Screening", to_name="Compliance/Case Manager"),
            ],
        ),
        ViewSpec(
            key="OpenBankingAccess",
            name="Open Banking Access",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="Third-party access via API Gateway with consent and identity validation",
            includes=[
                "Open Banking/API Gateway",
                "Open Banking/Consent Service",
                "Identity Provider/Auth Server",
                "Core Banking/Accounts Service",
            ],
            smart=True,
            filters=[
                IncludeRelByName(from_name="Open Banking/API Gateway", to_name="Identity Provider/Auth Server"),
                IncludeRelByName(from_name="Open Banking/API Gateway", to_name="Open Banking/Consent Service"),
                IncludeRelByName(from_name="Open Banking/API Gateway", to_name="Core Banking/Accounts Service"),
            ],
        ),
        ViewSpec(
            key="EventingOverview",
            name="Eventing Overview",
            view_type=ViewType.SYSTEM_LANDSCAPE,
            description="Event-driven backbone connecting producers and consumers",
            includes=[
                "Eventing/Kafka",
                "Notifications/Event Router",
                "Reporting/ETL Job",
                "Core Banking/Ledger Service",
                "Payments/Payments API",
            ],
            smart=True,
            filters=[
                IncludeRelByName(from_name="Core Banking/Ledger Service", to_name="Eventing/Kafka"),
                IncludeRelByName(from_name="Payments/Payments API", to_name="Eventing/Kafka"),
                IncludeRelByName(from_name="Eventing/Kafka", to_name="Notifications/Event Router"),
                IncludeRelByName(from_name="Eventing/Kafka", to_name="Reporting/ETL Job"),
            ],
        ),
    ]
