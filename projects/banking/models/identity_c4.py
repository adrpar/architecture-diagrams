from arch_diagrams.c4 import SystemLandscape, SoftwareSystem, Container

SYSTEM_KEY = "Identity Provider"


def define_identity(model: SystemLandscape) -> SoftwareSystem:
    _ = model + SoftwareSystem("Identity Provider", "Auth and identity management")
    idp = model["Identity Provider"]
    _ = idp + Container("Auth Server", "OAuth2/OIDC server", technology="Java")
    return idp


def link_identity(model: SystemLandscape) -> None:
    idp = model["Identity Provider"]
    portal = model["Customer Portal"]
    mobile = model["Mobile Banking"]
    model.relate(portal["Web App"], idp["Auth Server"], "Authenticates")
    model.relate(mobile["iOS App"], idp["Auth Server"], "Authenticates")
    model.relate(mobile["Android App"], idp["Auth Server"], "Authenticates")
