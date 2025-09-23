import os
from pathlib import Path

import pytest

from architecture_diagrams.orchestrator.build import build_workspace


def test_build_workspace_raises_when_no_internal_project_found():
    with pytest.raises(FileNotFoundError):
        build_workspace(project="__definitely_missing__", exporter="structurizr")


def test_build_workspace_raises_when_project_path_missing(tmp_path: Path):
    missing = tmp_path / "does-not-exist"
    assert not missing.exists()
    with pytest.raises(FileNotFoundError):
        build_workspace(project_path=missing, exporter="structurizr")


def test_build_workspace_raises_when_external_dir_has_no_models_or_views(tmp_path: Path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir(parents=True, exist_ok=True)
    # Ensure it's empty
    assert os.listdir(empty_dir) == []
    with pytest.raises(FileNotFoundError):
        build_workspace(project_path=empty_dir, exporter="structurizr")
