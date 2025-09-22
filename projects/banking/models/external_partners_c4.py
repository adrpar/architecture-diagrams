from architecture_diagrams.c4 import SystemLandscape, SoftwareSystem, Container

SYSTEM_KEY = "Clearing House"


def define_external_partners(model: SystemLandscape) -> SoftwareSystem:
    _ = model + SoftwareSystem("Clearing House", "External clearing network")
    ch = model["Clearing House"]
    _ = ch + Container("Clearing API", "External API", technology="HTTP")

    _ = model + SoftwareSystem("Email Provider", "External email service provider")
    ep = model["Email Provider"]
    _ = ep + Container("SMTP", "SMTP endpoint", technology="SMTP")

    _ = model + SoftwareSystem("SMS Gateway", "External SMS gateway")
    sg = model["SMS Gateway"]
    _ = sg + Container("SMPP", "SMPP endpoint", technology="SMPP")

    return ch


def link_external_partners(model: SystemLandscape) -> None:
    pay = model["Payments"]
    ch = model["Clearing House"]
    notif = model["Notifications"]
    ep = model["Email Provider"]
    sg = model["SMS Gateway"]
    model.relate(pay["Clearing Adapter"], ch["Clearing API"], "Submits payments")
    model.relate(notif["Email Service"], ep["SMTP"], "Sends emails")
    model.relate(notif["SMS Service"], sg["SMPP"], "Sends SMS")
