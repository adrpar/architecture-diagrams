from architecture_diagrams.c4 import Container, SoftwareSystem, SystemLandscape

SYSTEM_KEY = "Open Banking"


def define_open_banking(model: SystemLandscape) -> SoftwareSystem:
    _ = model + SoftwareSystem("Open Banking", "Third-party access via PSD2/Open Banking APIs")
    ob = model["Open Banking"]
    _ = ob + Container("API Gateway", "External API surface for TPPs", technology="Kong")
    _ = ob + Container("Consent Service", "Stores and validates user consents", technology="Go")
    return ob


def link_open_banking(model: SystemLandscape) -> None:
    ob = model["Open Banking"]
    core = model["Core Banking"]
    idp = model["Identity Provider"]
    # TPPs authenticate via IDP, then call API Gateway. Gateway calls Core services.
    model.relate(ob["API Gateway"], idp["Auth Server"], "Validates tokens")
    model.relate(ob["API Gateway"], ob["Consent Service"], "Checks consent")
    model.relate(ob["API Gateway"], core["Accounts Service"], "Reads account data")
