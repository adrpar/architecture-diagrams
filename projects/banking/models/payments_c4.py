from architecture_diagrams.c4 import SystemLandscape, SoftwareSystem, Container

SYSTEM_KEY = "Payments"


def define_payments(model: SystemLandscape) -> SoftwareSystem:
    _ = model + SoftwareSystem("Payments", "Payments processing and clearing")
    pay = model["Payments"]
    _ = pay + Container("Payments API", "REST API for payments", technology="Go")
    _ = pay + Container("Clearing Adapter", "Clearinghouse connectivity", technology="Go")
    _ = pay + Container("Fraud Service", "Fraud detection", technology="Python")
    _ = pay + Container("Payments DB", "Payments data store", technology="PostgreSQL")
    return pay


def link_payments(model: SystemLandscape) -> None:
    pay = model["Payments"]
    core = model["Core Banking"]
    portal = model["Customer Portal"]
    mobile = model["Mobile Banking"]

    model.relate(portal["Web App"], pay["Payments API"], "Initiates payments")
    model.relate(mobile["iOS App"], pay["Payments API"], "Initiates payments")
    model.relate(mobile["Android App"], pay["Payments API"], "Initiates payments")
    model.relate(pay["Payments API"], core["Accounts Service"], "Verifies account & balance")
    model.relate(pay["Clearing Adapter"], pay["Payments API"], "Reports clearing status")
    model.relate(pay["Fraud Service"], pay["Payments API"], "Scores transactions")
    model.relate(pay["Payments API"], pay["Payments DB"], "Reads/Writes")
