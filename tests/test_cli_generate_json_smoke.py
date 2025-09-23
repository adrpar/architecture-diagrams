import json
from pathlib import Path

from click.testing import CliRunner

from architecture_diagrams.archdiags import cli


def test_generate_json_smoke_tmp(tmp_path: Path):
    out = tmp_path / "smoke.json"
    runner = CliRunner()
    res = runner.invoke(
        cli,
        [
            "generate",
            "--project",
            "banking",
            "--exporter",
            "json",
            "--output",
            str(out),
        ],
    )
    assert res.exit_code == 0, res.output
    assert out.exists()
    data = json.loads(out.read_text())
    # Basic shape assertions
    assert isinstance(data, dict)
    for key in ("name", "systems", "relationships"):
        assert key in data
    assert isinstance(data["systems"], list)
    assert isinstance(data["relationships"], list)
