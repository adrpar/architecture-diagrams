from architecture_diagrams.orchestrator.loader import discover_model_builders
from architecture_diagrams.orchestrator.compose import compose
from architecture_diagrams.adapter.pystructurizr_export import dump_dsl
from pathlib import Path


def build_c4_workspace():
    root = Path(__file__).resolve().parents[1]
    builders = discover_model_builders(root, project="banking")
    return compose(builders, name="banking")


def test_c4_workspace_contains_core_systems():
    wm = build_c4_workspace()
    systems = {s.name for s in wm.software_systems.values()}
    assert {
        "Payments",
        "Core Banking",
        "Customer Portal",
        "Mobile Banking",
        "Identity Provider",
        "Reporting",
        "Notifications",
        "Eventing",
        "Open Banking",
        "Risk & ML",
        "Compliance",
        "Clearing House",
        "Email Provider",
        "SMS Gateway",
    }.issubset(systems)


def test_payments_core_relationships():
    wm = build_c4_workspace()
    def has(src, dst, desc):
        return any(r.source.name == src and r.destination.name == dst and r.description == desc for r in wm.relationships)
    assert has("Web App", "Payments API", "Initiates payments")
    assert has("Payments API", "Accounts Service", "Verifies account & balance")
    assert has("Clearing Adapter", "Payments API", "Reports clearing status")
    assert has("Fraud Service", "Payments API", "Scores transactions")
    assert has("Payments API", "Payments DB", "Reads/Writes")


def test_identity_relationships():
    wm = build_c4_workspace()
    def has(src, dst, desc):
        return any(r.source.name == src and r.destination.name == dst and r.description == desc for r in wm.relationships)
    assert has("Web App", "Auth Server", "Authenticates")
    assert has("iOS App", "Auth Server", "Authenticates")
    assert has("Android App", "Auth Server", "Authenticates")


def test_eventing_relationships():
    wm = build_c4_workspace()
    def has(src, dst, desc_sub):
        return any(r.source.name == src and r.destination.name == dst and desc_sub in r.description for r in wm.relationships)
    assert has("Ledger Service", "Kafka", "Publishes posting events")
    assert has("Payments API", "Kafka", "Publishes payment events")
    assert has("Kafka", "Event Router", "Delivers events")
    assert has("Kafka", "ETL Job", "Feeds analytics")


def test_notifications_reporting_open_banking_and_risk_relationships():
    wm = build_c4_workspace()
    def has(src, dst, desc):
        return any(r.source.name == src and r.destination.name == dst and r.description == desc for r in wm.relationships)
    # Notifications
    assert has("Payments API", "Event Router", "Emits payment events")
    # Reporting
    assert has("ETL Job", "Accounts Service", "Extracts accounts")
    assert has("ETL Job", "Payments API", "Extracts transactions")
    # Open Banking
    assert has("API Gateway", "Auth Server", "Validates tokens")
    assert has("API Gateway", "Consent Service", "Checks consent")
    assert has("API Gateway", "Accounts Service", "Reads account data")
    # Risk & ML
    assert has("Fraud Service", "Model Serving", "Requests fraud scores")
    assert has("Training Pipeline", "ETL Job", "Consumes historical data")
    assert has("Feature Store", "Model Serving", "Provides features")


def test_aml_and_external_partners_relationships():
    wm = build_c4_workspace()
    def has(src, dst, desc):
        return any(r.source.name == src and r.destination.name == dst and r.description == desc for r in wm.relationships)
    # AML
    assert has("Accounts Service", "KYC Service", "Requests KYC checks")
    assert has("Payments API", "Sanctions Screening", "Screens counterparties")
    assert has("KYC Service", "Case Manager", "Escalates suspicious profiles")
    assert has("Sanctions Screening", "Case Manager", "Creates sanctions investigation case")
    # External partners
    assert has("Clearing Adapter", "Clearing API", "Submits payments")
    assert has("Email Service", "SMTP", "Sends emails")
    assert has("SMS Service", "SMPP", "Sends SMS")


def test_workspace_dsl_has_views_block():
    wm = build_c4_workspace()
    dsl = dump_dsl(wm)
    assert "views {" in dsl
