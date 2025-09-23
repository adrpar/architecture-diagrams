from architecture_diagrams.c4 import SystemLandscape, ViewType
from architecture_diagrams.orchestrator.specs import ViewSpec


def test_view_spec_includes_container_path_falls_back_to_system_when_missing():
    m = SystemLandscape("Spec")
    s = m.add_software_system("Sys", "")
    spec = ViewSpec(
        key="land",
        name="Landscape",
        view_type=ViewType.SYSTEM_LANDSCAPE,
        includes=["Sys/DoesNotExist"],
    )
    spec.build(m)
    # Should include the system id (fallback) rather than erroring
    view = next(v for v in m.views if v.key == "land")
    assert s.id in view.include
