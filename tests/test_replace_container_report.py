from architecture_diagrams.c4 import SystemLandscape


def test_replace_container_report_rewire_and_flags():
    m = SystemLandscape("Repl")
    s = m.add_software_system("Sys", "")
    old = s.add_container("Kafka", "", "Kafka")
    new_name = "Redis Queue"
    a = s.add_container("API", "", "Python")
    b = s.add_container("Worker", "", "Python")
    # Relationships involving old
    m.add_relationship(a, old, "pub")
    m.add_relationship(old, b, "sub")

    res = m.replace_container_report(
        "Sys",
        "Kafka",
        new_name,
        description="Message queue",
        technology="Redis",
        tag_new=["queue"],
        tag_old=["deprecated"],
        remove_old=True,
    )

    assert res.new_container.name == new_name
    assert res.old_container is old
    assert res.rewired_count == 2
    assert res.removed_old is True
    assert res.created_new is True
    # Ensure relationships now point to new
    pairs = {(r.source.name, r.destination.name) for r in m.relationships}
    assert ("API", new_name) in pairs and (new_name, "Worker") in pairs
    # Old tag updated
    assert "deprecated" in old.tags
