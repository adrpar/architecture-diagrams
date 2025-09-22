from __future__ import annotations

from architecture_diagrams.orchestrator.build import build_workspace_dsl


def test_inherited_view_is_emitted_and_annotated():
    dsl = build_workspace_dsl(project="banking_redis", workspace_name="Banking (Redis Eventing Variant)")

    # The inherited view should be present; our exporter annotates each view with key/name as a comment
    assert 'View: key="EventingOverviewRedisInherited" name="Eventing Overview (Redis, inherited)"' in dsl

    # Also sanity check the explicit Redis view exists
    assert 'description "Event-driven backbone connecting producers and consumers via Redis Queue"' in dsl
