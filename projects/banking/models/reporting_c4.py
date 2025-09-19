from arch_diagrams.c4 import SystemLandscape, SoftwareSystem, Container

SYSTEM_KEY = "Reporting"


def define_reporting(model: SystemLandscape) -> SoftwareSystem:
    _ = model + SoftwareSystem("Reporting", "Analytics and reporting")
    rep = model["Reporting"]
    _ = rep + Container("ETL Job", "Loads data into warehouse", technology="Python")
    _ = rep + Container("BI Tool", "Dashboards and reports", technology="SaaS")
    return rep


def link_reporting(model: SystemLandscape) -> None:
    rep = model["Reporting"]
    core = model["Core Banking"]
    pay = model["Payments"]
    model.relate(rep["ETL Job"], core["Accounts Service"], "Extracts accounts")
    model.relate(rep["ETL Job"], pay["Payments API"], "Extracts transactions")
