from architecture_diagrams.c4 import SystemLandscape
from typing import Mapping, Union, cast


def test_ensure_containers_from_map_creates_and_registers():
    wm = SystemLandscape("Test", "")
    sys = wm.add_software_system("example", "Example system")
    raw_spec: dict[str, dict[str, object]] = {
        "api": {"desc": "API service", "tech": "Python"},
        "fe": {"desc": "Frontend", "tech": None},
    }
    spec = cast(Mapping[str, Union[tuple[str, str | None], Mapping[str, object]]], raw_spec)
    # Create containers from mapping (mirrors removed helper logic)
    for name, meta in spec.items():
        if isinstance(meta, tuple):  # pragma: no cover (not used in this test input)
            desc, tech = meta
        else:
            desc = cast(str, meta.get("desc", ""))  # type: ignore[index]
            tech = cast(Union[str, None], meta.get("tech"))  # type: ignore[index]
        # Idempotent: add only if missing
        existing = next((c for c in sys.containers if c.name == name), None)
        if not existing:
            sys.add_container(name, desc, tech)
    # Containers exist in system
    names = {c.name for c in sys.containers}
    assert names == set(spec.keys())
    # Registry lookups
    api = wm.get_container("example", "api")
    fe = wm.get_container("example", "fe")
    assert api.description == "API service"
    assert fe.technology is None


def test_ensure_containers_from_map_idempotent():
    wm = SystemLandscape("Test2", "")
    sys = wm.add_software_system("sample", "Sample system")
    raw_spec: dict[str, dict[str, object]] = {"svc": {"desc": "Svc", "tech": None}}
    spec = cast(Mapping[str, Union[tuple[str, str | None], Mapping[str, object]]], raw_spec)
    def ensure_containers_from_map_local():
        created: dict[str, object] = {}
        for name, meta in spec.items():
            if isinstance(meta, tuple):  # pragma: no cover
                desc, tech = meta
            else:
                desc = cast(str, meta.get("desc", ""))  # type: ignore[index]
                tech = cast(Union[str, None], meta.get("tech"))  # type: ignore[index]
            found = next((c for c in sys.containers if c.name == name), None)
            if not found:
                found = sys.add_container(name, desc, tech)
            created[name] = found
        return created

    first = ensure_containers_from_map_local()
    second = ensure_containers_from_map_local()
    assert set(first.keys()) == {"svc"}
    assert set(second.keys()) == {"svc"}
    # Idempotent: same container object instance
    assert first["svc"] is second["svc"]
    svc_list = [c for c in sys.containers if c.name == "svc"]
    assert len(svc_list) == 1
