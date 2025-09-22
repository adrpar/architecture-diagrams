from architecture_diagrams.c4 import SystemLandscape, Container


def test_system_indexing_and_container_lookup():
    model = SystemLandscape("Idx", "")
    sys = model.add_software_system("Demo", "Demo system")
    # add via proxy
    c1 = model["Demo"].add_container("api", "Public API", "FastAPI")
    # adopt pre-created container using + (system + container)
    worker = Container("worker", "Worker", "Python")
    sys + worker  # adopt via + operator using direct SoftwareSystem reference
    # direct tuple indexing syntax and slash syntax
    assert model["Demo"]["api"] is c1
    assert model["Demo/api"] is c1
    # ensure adopted container present
    assert any(c.name == "worker" for c in sys.containers)
    assert model["Demo"]["worker"].description == "Worker"


def test_operator_relationship_pairs_and_relate():
    model = SystemLandscape("Ops")
    s = model.add_software_system("Core", "")
    a = s.add_container("A", "", "Python")
    b = s.add_container("B", "", "Python")
    # forward and reverse pairs
    forward = a >> b
    reverse = a << b
    assert forward == (a, b)
    assert reverse == (b, a)
    model.relate(forward, "calls")
    model.relate(reverse, "responds to")
    descs = {r.description for r in model.relationships}
    assert {"calls", "responds to"}.issubset(descs)


def test_add_container_idempotent_and_index_refresh():
    model = SystemLandscape("IdxRefresh")
    s = model.add_software_system("Sys", "")
    c = s.add_container("api", "", "Python")
    # add again with extra metadata; should update description/tech only if previously empty
    again = s.add_container("api", "New Desc", "Go")
    assert again is c
    # description/technology shouldn't overwrite non-empty ones
    assert c.technology == "Python"
    # use model indexing after second call
    assert model["Sys"]["api"] is c

