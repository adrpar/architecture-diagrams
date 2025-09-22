from __future__ import annotations

from architecture_diagrams.orchestrator.build import build_workspace_dsl


def test_extends_key_overrides_base_view():
    dsl = build_workspace_dsl(project="banking_redis", workspace_name="Banking (Redis Eventing Variant)")

    # The derived view should exist
    assert 'View: key="EventingOverviewRedisInherited" name="Eventing Overview (Redis, inherited)"' in dsl

    # The base view should be replaced (not present as a separate view)
    # We detect the base view by its annotation line; it should not appear
    assert 'View: key="EventingOverview" name="Eventing Overview"' not in dsl
