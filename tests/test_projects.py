from __future__ import annotations

from pathlib import Path

from architecture_diagrams.orchestrator.build import build_workspace_dsl


def test_banking_is_supported(tmp_path: Path) -> None:
    dsl = build_workspace_dsl(project="banking", workspace_name="banking")
    assert isinstance(dsl, str)
    assert "workspace" in dsl
    assert "Core Banking" in dsl or "Banking" in dsl
    assert "views {" in dsl
