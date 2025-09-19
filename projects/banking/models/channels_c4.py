from arch_diagrams.c4 import SystemLandscape, SoftwareSystem, Container

# Primary system used for existence check in link phase
SYSTEM_KEY = "Customer Portal"


def define_channels(model: SystemLandscape) -> SoftwareSystem:
    _ = model + SoftwareSystem("Customer Portal", "Web banking portal")
    portal = model["Customer Portal"]
    _ = portal + Container("Web App", "Customer web portal", technology="Next.js")

    _ = model + SoftwareSystem("Mobile Banking", "Mobile app for banking")
    mobile = model["Mobile Banking"]
    _ = mobile + Container("iOS App", "Native iOS app", technology="Swift")
    _ = mobile + Container("Android App", "Native Android app", technology="Kotlin")

    return portal


def link_channels(model: SystemLandscape) -> None:
    # Relationships wired in payments and identity
    pass
