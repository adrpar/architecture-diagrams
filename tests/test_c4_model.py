from architecture_diagrams.c4 import SystemLandscape


def test_workspace_model_basic_elements_and_ids():
    wm = SystemLandscape("Test Workspace", "Desc")
    person = wm.add_person("Alice", "User")
    system = wm.add_software_system("Payment API", "Processes payments")
    container = system.add_container("API Service", "Handles REST API", "Python")
    component = container.add_component("Controller", "Routes requests", "FastAPI")

    # Duplicate name to force id disambiguation
    wm.add_person("Alice", "Another user")  # should become alice-2

    ids = [e.id for e in wm.iter_elements()]
    assert person.id == "alice"
    assert "alice-2" in ids
    assert system.id == "payment-api"
    assert container.id == "api-service"
    assert component.id == "controller"


def test_relationship_and_views():
    wm = SystemLandscape("Rel Test")
    p = wm.add_person("User", "")
    s = wm.add_software_system("Portal", "")
    c = s.add_container("Frontend", "", "Next.js")
    wm.add_relationship(p, s, "uses", "HTTPS")

    v = wm.add_system_landscape_view("landscape", "Landscape")
    v.add(p)
    v.add(s)

    cv = wm.add_container_view("portalContainers", "Portal Containers", s)
    cv.add(c)

    # Ensure relationships stored and view includes propagate
    assert len(wm.relationships) == 1
    assert {p.id, s.id}.issubset(v.include)
    assert c.id in cv.include


def test_iter_elements_contains_all():
    wm = SystemLandscape("Iter")
    p = wm.add_person("Bob", "")
    s = wm.add_software_system("CRM", "")
    cont = s.add_container("Backend", "", "Python")
    comp = cont.add_component("Repo", "", "SQLAlchemy")

    ids = {e.id for e in wm.iter_elements()}
    assert {p.id, s.id, cont.id, comp.id}.issubset(ids)


def test_deployment_and_infrastructure_nodes():
    wm = SystemLandscape("Deploy")
    s = wm.add_software_system("Ordering", "")
    api = s.add_container("API", "", "Python")
    dep = wm.add_deployment_node("Kubernetes Cluster", "")
    pod = dep.add_deployment_node("Pod", "")
    dep.add_infrastructure_node("Ingress", "", "NGINX")
    pod.add_container_instance(api)
    # Ensure traversal includes deployment structures
    names = {e.name for e in wm.iter_elements()}
    assert {"Kubernetes Cluster", "Pod", "Ingress", "Ordering", "API"}.issubset(names)
