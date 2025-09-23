from architecture_diagrams.c4 import SystemLandscape


def test_add_container_tags_creation_normalizes_string_and_iterable():
    wm = SystemLandscape("TagsCreate")
    s = wm.add_software_system("Sys", "")
    # String tag should normalize to a singleton set
    c1 = s.add_container("A", "", None, tags="proposed")
    assert c1.tags == {"proposed"}
    # Iterable tags should become a set and deduplicate
    c2 = s.add_container("B", "", None, tags=["a", "b", "a"])  # type: ignore[list-item]
    assert c2.tags == {"a", "b"}


def test_add_container_tags_update_existing_and_desc_merge():
    wm = SystemLandscape("TagsUpdate")
    s = wm.add_software_system("Sys", "")
    c = s.add_container("api", "", "Python")
    # Update with a string tag
    again = s.add_container("api", "New Desc", "Go", tags="proposed")
    assert again is c
    assert "proposed" in c.tags
    # Description should be updated because it was initially empty
    assert c.description == "New Desc"
    # Technology should not be overwritten because it was already set
    assert c.technology == "Python"
    # Update with an iterable of tags (merge)
    s.add_container("api", "", None, tags=["x", "y"])  # type: ignore[list-item]
    assert {"proposed", "x", "y"}.issubset(c.tags)
