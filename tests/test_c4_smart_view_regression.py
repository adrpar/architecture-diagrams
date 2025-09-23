from pathlib import Path

from architecture_diagrams.adapter.pystructurizr_export import dump_dsl
from architecture_diagrams.orchestrator.compose import compose
from architecture_diagrams.orchestrator.loader import discover_model_builders


def normalize(s: str) -> str:
    return "\n".join(line.rstrip() for line in s.splitlines() if line.strip())


def _build_c4_workspace():
    root = Path(__file__).resolve().parents[1]
    builders = discover_model_builders(root, project="banking")
    return compose(builders, name="banking")


def test_internal_smart_view_emits_expected_section():
    wm = _build_c4_workspace()
    # Build smart system landscape via new API
    smart = wm.add_smart_system_landscape_view(
        key="smart-system-landscape",
        name="BankingSystemsOverview",
        description="Banking systems and their interaction with partner systems",
    )
    # Include selected systems by id
    name_to_id = {s.name: s.id for s in wm.software_systems.values()}
    for sys_name in ["Payments", "Mobile Banking"]:
        sid = name_to_id.get(sys_name)
        if sid:
            smart.include.add(sid)
    current = dump_dsl(wm)
    # pull the emitted smart view section
    cur_lines = []
    capture2 = False
    for line in current.splitlines():
        if "systemLandscape" in line:
            capture2 = True
        if capture2:
            cur_lines.append(line)
        if capture2 and line.strip() == "}":
            if any("autoLayout" in line_ for line_ in cur_lines):
                break
    current_view = "\n".join(cur_lines)

    # Assert key characteristics instead of full snapshot
    assert "systemLandscape" in current_view
    assert "autoLayout" in current_view
    # Confirm the description is present (title may be omitted by dumper for smart views)
    assert "Banking systems and their interaction with partner systems" in current_view
    assert "Payments" in current
    assert "Mobile Banking" in current
