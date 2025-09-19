from arch_diagrams.c4 import SystemLandscape, SoftwareSystem, Container

SYSTEM_KEY = "Compliance"


def define_aml(model: SystemLandscape) -> SoftwareSystem:
    _ = model + SoftwareSystem("Compliance", "KYC/AML, sanctions screening and case management")
    comp = model["Compliance"]
    _ = comp + Container("KYC Service", "Performs KYC/KYB checks", technology="Python")
    _ = comp + Container("Sanctions Screening", "Screens parties against sanctions lists", technology="Python")
    _ = comp + Container("Case Manager", "Manages manual reviews and SARs", technology="Java")
    return comp


def link_aml(model: SystemLandscape) -> None:
    comp = model["Compliance"]
    core = model["Core Banking"]
    pay = model["Payments"]
    # KYC checks on account creation and payment initiation
    model.relate(core["Accounts Service"], comp["KYC Service"], "Requests KYC checks")
    model.relate(pay["Payments API"], comp["Sanctions Screening"], "Screens counterparties")
    # Escalations to case management
    model.relate(comp["KYC Service"], comp["Case Manager"], "Escalates suspicious profiles")
    model.relate(comp["Sanctions Screening"], comp["Case Manager"], "Creates sanctions investigation case")