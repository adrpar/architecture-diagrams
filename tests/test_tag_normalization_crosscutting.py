from architecture_diagrams.c4 import SystemLandscape


def test_add_relationship_tags_string_normalizes_to_singleton():
    m = SystemLandscape("RelTags")
    a = m.add_person("User", "")
    s = m.add_software_system("Sys", "")
    r = m.add_relationship(a, s, "uses", technology="HTTP", tags="proposed")
    assert r.tags == {"proposed"}


def test_deployment_and_infra_tags_string_normalizes_to_singleton():
    m = SystemLandscape("DeployTags")
    d = m.add_deployment_node("Cluster", "", technology="k8s", tags="prod")
    i = d.add_infrastructure_node("Ingress", "", technology="nginx", tags="edge")
    assert d.tags == {"prod"}
    assert i.tags == {"edge"}
