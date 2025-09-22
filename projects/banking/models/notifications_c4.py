from architecture_diagrams.c4 import SystemLandscape, SoftwareSystem, Container

SYSTEM_KEY = "Notifications"


def define_notifications(model: SystemLandscape) -> SoftwareSystem:
    _ = model + SoftwareSystem("Notifications", "Outbound messaging and alerts")
    svc = model["Notifications"]
    _ = svc + Container("Event Router", "Routes events to channels", technology="Go")
    _ = svc + Container("Email Service", "Sends emails", technology="Python")
    _ = svc + Container("SMS Service", "Sends SMS", technology="Python")
    return svc


def link_notifications(model: SystemLandscape) -> None:
    svc = model["Notifications"]
    pay = model["Payments"]
    core = model["Core Banking"]
    # Payments emits events, notifications fan out
    model.relate(pay["Payments API"], svc["Event Router"], "Emits payment events")
    model.relate(core["Ledger Service"], svc["Event Router"], "Emits posting events")
