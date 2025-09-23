from architecture_diagrams.c4 import SystemLandscape


def test_limit_relationships_context_manager_filters_temporarily():
    m = SystemLandscape("RelCtx")
    a = m.add_software_system("A", "")
    b = m.add_software_system("B", "")
    c = m.add_software_system("C", "")
    m.add_relationship(a, b, "calls")
    m.add_relationship(b, c, "calls")
    m.add_relationship(a, c, "calls")

    # Outside context: all relationships
    assert len(list(m.get_effective_relationships())) == 3

    with m.limit_relationships_to({("A", "B"), ("B", "C")}):
        pairs = {(r.source.name, r.destination.name) for r in m.get_effective_relationships()}
        assert pairs == {("A", "B"), ("B", "C")}

    # After context: all restored
    assert len(list(m.get_effective_relationships())) == 3
