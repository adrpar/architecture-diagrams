from architecture_diagrams.c4 import SystemLandscape
from architecture_diagrams.c4.auto_two_phase import auto_register, auto_register_all


def test_auto_register_single_define_and_link():
    model = SystemLandscape("banking")
    # payments links depend on Core Banking and Channels (Customer Portal/Mobile Banking)
    auto_register(model, "channels", phase="define", project="banking")
    auto_register(model, "core", phase="define", project="banking")
    _ = auto_register(model, "payments", project="banking")  # runs define + link
    assert any(s.name == "Payments" for s in model.software_systems.values())
    rels = {(r.source.name, r.destination.name, r.description) for r in model.relationships}
    assert (
        ("Web App", "Payments API", "Initiates payments") in {(s,d,desc) for (s,d,desc) in rels} or
        any("Verifies account" in desc for (_,_,desc) in rels) or
        any("Reads/Writes" == desc for (_,_,desc) in rels)
    )


def test_auto_register_define_only_then_link():
    model = SystemLandscape("banking")
    # identity links depend on channels (Customer Portal/Mobile Banking)
    auto_register(model, "channels", phase="define", project="banking")
    auto_register(model, "identity", phase="define", project="banking")
    auto_register(model, "identity", phase="link", project="banking")
    assert any(s.name == "Identity Provider" for s in model.software_systems.values())


def test_auto_register_all_mixed():
    model = SystemLandscape("banking")
    auto_register_all(model, ["channels", "core", "payments"], phase="define", project="banking")
    auto_register(model, "payments", phase="link", project="banking")
    assert any(s.name == "Payments" for s in model.software_systems.values())
