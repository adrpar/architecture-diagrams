from architecture_diagrams.c4 import SystemLandscape


def test_groups_assign_get_unassign_unique():
    m = SystemLandscape("Groups")
    s1 = m.add_software_system("S1", "")
    s2 = m.add_software_system("S2", "")
    m.assign_group("A", s1)
    m.assign_group("A", s1)  # duplicate; should not duplicate
    m.assign_group("A", s2)
    assert [s.name for s in m.get_group("A")] == ["S1", "S2"]
    m.unassign_group("A", s1)
    assert [s.name for s in m.get_group("A")] == ["S2"]


def test_unified_getter_and_view_sugar():
    m = SystemLandscape("Get")
    p = m.add_person("User", "")
    s = m.add_software_system("Core", "")
    c = s.add_container("API", "", "Python")
    # get() variants
    assert m.get("Core") is s
    assert m.get("Core/API") is c
    assert m.get("person:User") is p
    # auto-view helpers
    ctx = m.add_context_view_for(s)
    cont = m.add_container_view_for(s)
    assert ctx.key == "CoreContext"
    assert cont.key == "CoreContainers"
