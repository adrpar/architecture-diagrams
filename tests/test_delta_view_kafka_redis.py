from __future__ import annotations

import re

from architecture_diagrams.orchestrator.build import build_workspace_dsl


def _extract_view_block(dsl: str, view_key: str) -> str:
    """Return the text of the first view block that matches the given key annotation."""
    # Find the annotated header comment for the view
    marker = f'// View: key="{view_key}"'
    start = dsl.find(marker)
    assert start != -1, f"View with key {view_key} not found in DSL"
    # Backtrack to the beginning of the enclosing view block (systemLandscape { ... })
    block_start = dsl.rfind("systemLandscape", 0, start)
    assert block_start != -1, "Expected a systemLandscape view block"
    # Find the end of the block by matching closing brace
    brace_open = dsl.find("{", block_start)
    depth = 0
    i = brace_open
    while i < len(dsl):
        if dsl[i] == "{":
            depth += 1
        elif dsl[i] == "}":
            depth -= 1
            if depth == 0:
                return dsl[block_start : i + 1]
        i += 1
    raise AssertionError("Unterminated view block")


def test_delta_view_shows_kafka_node_without_edges():
    dsl = build_workspace_dsl(
        project="banking_redis", workspace_name="Banking (Redis Eventing Variant)"
    )

    # Kafka container remains in the model (deprecated), ensure it's declared
    assert re.search(r"^\s*kafka\s*=\s*Container\s+\"Kafka\"", dsl, re.MULTILINE)

    # In the Delta view block, Kafka should have no edges, while Redis edges are present
    delta_block = _extract_view_block(dsl, "EventingDeltaKafkaToRedis")
    assert "redis_queue->event_router" in delta_block
    assert "ledger_service->redis_queue" in delta_block
    assert "payments_api->redis_queue" in delta_block
    # No Kafka edges included
    assert "kafka->" not in delta_block
    assert "-> kafka" not in delta_block


def test_redis_overview_vs_inherited_are_distinct():
    dsl = build_workspace_dsl(
        project="banking_redis", workspace_name="Banking (Redis Eventing Variant)"
    )

    # Inherited view includes Redis -> ETL, explicit overview omits it
    inherited_block = _extract_view_block(dsl, "EventingOverviewRedisInherited")
    explicit_block = _extract_view_block(dsl, "EventingRedisOverview")

    assert "redis_queue->etl_job" in inherited_block
    assert "redis_queue->etl_job" not in explicit_block
