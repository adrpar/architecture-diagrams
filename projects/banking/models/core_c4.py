from arch_diagrams.c4 import SystemLandscape, SoftwareSystem, Container

SYSTEM_KEY = "Core Banking"


def define_core(model: SystemLandscape) -> SoftwareSystem:
    _ = model + SoftwareSystem("Core Banking", "Accounts, balances, and ledger")
    core = model["Core Banking"]
    _ = core + Container("Accounts Service", "Holds account data", technology="Java")
    _ = core + Container("Ledger Service", "Double-entry ledger", technology="Java")
    _ = core + Container("Risk Engine", "Risk scoring and limits", technology="Python")
    _ = core + Container("Accounts DB", "Accounts database", technology="PostgreSQL")
    _ = core + Container("Ledger DB", "Ledger database", technology="PostgreSQL")
    return core


def link_core(model: SystemLandscape) -> None:
    core = model["Core Banking"]
    # Internal dependencies
    model.relate(core["Accounts Service"], core["Accounts DB"], "Reads/Writes")
    model.relate(core["Ledger Service"], core["Ledger DB"], "Reads/Writes")
